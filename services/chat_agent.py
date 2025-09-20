"""chat_agent service

This module provides a `run_chat_agent` coroutine which:
- fetches context data from Google BigQuery
- performs a web search (optional, via SerpAPI) to enrich context
- composes the context with the user's query and calls a LangChain LLM

Environment variables expected:
- `GOOGLE_APPLICATION_CREDENTIALS` : path to GCP credentials JSON (used by BigQuery client)
- `SERPAPI_API_KEY` (optional) : SerpAPI key for web search
- `GOOGLE_GENAI_MODEL` (optional) : model name for ChatGoogleGenerativeAI (default: "gemini-2.5-flash")

Install suggestions:
    pip install google-cloud-bigquery requests python-dotenv langchain-google-genai langchain-core

Usage example (async):
    from services.chat_agent import run_chat_agent
    result = await run_chat_agent(user_query="Analyze revenue trends for startup X", bq_query="SELECT ... LIMIT 10")
"""

from typing import Optional, List
import os
import json
import dotenv
import asyncio

from google.cloud import bigquery
from services.gcp_utils import get_bq_client
import requests

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory

dotenv.load_dotenv()

# Configuration
GOOGLE_GENAI_MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
GEMINI_WEB_SEARCH = os.getenv("GEMINI_WEB_SEARCH", "false").lower() in ("1", "true", "yes")

# instantiate module-level LLM used by tools/agent
llm = ChatGoogleGenerativeAI(model=GOOGLE_GENAI_MODEL, temperature=0.2)


def fetch_bigquery(bq_sql: str, project: Optional[str] = None, max_rows: int = 100) -> List[dict]:
    """Run a BigQuery SQL query and return rows as list of dicts.

    Requires `GOOGLE_APPLICATION_CREDENTIALS` env var or default application credentials.
    """
    client = bigquery.Client(project=project)
    query_job = client.query(bq_sql)
    results = query_job.result(max_results=max_rows)
    return [dict(row) for row in results]


def serpapi_search(query: str, num: int = 5) -> List[str]:
    """Simple SerpAPI web search that returns the top result snippets (if API key provided).

    Falls back to empty list if SERPAPI_API_KEY not set.
    """
    if not SERPAPI_API_KEY:
        return []
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": num,
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    snippets = []
    for item in data.get("organic_results", [])[:num]:
        snippet = item.get("snippet") or item.get("title")
        if snippet:
            snippets.append(snippet)
    return snippets


def _tool_create(name: str, system_role: str, description: str, task_prefix: str):
    """Helper to create a Tool that calls the module LLM with a system role and a task-specific prompt."""
    def tool_func(input_text: str) -> str:
        # Use the LLM to perform the tool task synchronously
        prompt = [SystemMessage(content=system_role), HumanMessage(content=f"{task_prefix}: {input_text}")]
        resp = llm.invoke(prompt)
        # prefer content attribute if present
        return getattr(resp, "content", str(resp))

    return Tool(name=name, func=tool_func, description=description)


# Tool: BigQuery query executor
def _bigquery_tool_func(sql: str) -> str:
    try:
        rows = fetch_bigquery(sql)
        # return JSON string of rows (truncate to avoid huge responses)
        return json.dumps(rows[:50], default=str)
    except Exception as e:
        return f"BigQuery error: {e}"


bigquery_tool = Tool(name="bigquery_query", func=_bigquery_tool_func, description="Execute a BigQuery SQL and return top rows as JSON")


# Tool: Web search wrapper (SerpAPI)
def _web_search_tool_func(query: str) -> str:
    snippets = serpapi_search(query, num=5)
    if not snippets and GEMINI_WEB_SEARCH:
        # hint: model-side browsing might be available in some environments
        return ""  # empty -> agent may still try model browsing if configured
    return "\n---\n".join(snippets)


web_search_tool = Tool(name="web_search", func=_web_search_tool_func, description="Perform a web search and return top snippets")


# Optional helper: Summarize context
summarize_tool = _tool_create(
    name="summarize",
    system_role="You are a concise summarizer.",
    description="Summarize input text into a short bullet list",
    task_prefix="Summarize"
)


# Agent memory and initialization
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

chat_agent_agent = initialize_agent(
    tools=[bigquery_tool, web_search_tool, summarize_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True,
)


async def run_chat_agent(user_query: str, bq_sql: Optional[str] = None, project: Optional[str] = None) -> dict:
    """Main entrypoint: fetch context, perform web search, call LLM and return the result.

    - `user_query`: user's question or instruction.
    - `bq_sql`: optional BigQuery SQL to run and include as context. If omitted, BQ step is skipped.
    - `project`: optional GCP project override for BigQuery client.
    """
    bq_context = None
    web_snippets = None

    if bq_sql:
        # run BigQuery in threadpool to avoid blocking event loop
        loop = asyncio.get_running_loop()
        bq_context = await loop.run_in_executor(None, fetch_bigquery, bq_sql, project)

    # run web search (best-effort)
    web_snippets = await asyncio.get_running_loop().run_in_executor(None, serpapi_search, user_query)

    # Enforce that web search must be present in the context
    if not web_snippets:
        # If GEMINI_WEB_SEARCH is enabled, the developer may be expecting the model to fetch the web itself.
        # That requires special model tooling or browsing access. If not enabled, fail fast and instruct user.
        if GEMINI_WEB_SEARCH:
            raise RuntimeError(
                "Web search returned no snippets. You enabled GEMINI_WEB_SEARCH but automatic browsing is not configured. "
                "Configure model browsing/tooling in your Google GenAI account or provide SERPAPI_API_KEY for external search.")
        else:
            raise RuntimeError(
                "Web search is mandatory for this agent but no search results were obtained.\n"
                "Provide a valid SerpAPI key in `SERPAPI_API_KEY` environment variable or enable Gemini web browsing.\n"
                "To use SerpAPI: export SERPAPI_API_KEY=your_key\n"
                "To enable Gemini web browsing: set GEMINI_WEB_SEARCH=true and configure browsing in the Google GenAI SDK (if available).")

    # Build agent prompt instructing it to use tools when needed
    agent_prompt = f"""
You are a helpful startup analysis agent. You have access to tools: `bigquery_query` (executes SQL), `web_search` (fetches web snippets), and `summarize`.
Rules:
- Always try to use `web_search` to enrich answers with up-to-date information.
- Use `bigquery_query` when the user requests data contained in the dataset. When using it, call with a SQL query.
- Use `summarize` to compress long contexts.

User query: {user_query}

If a BigQuery SQL was provided, here it is:\n{bq_sql if bq_sql else 'None'}
Return a concise, actionable response and list which tools you used.
"""

    # Run the agent synchronously in a threadpool (initialize_agent returns a sync agent)
    loop = asyncio.get_running_loop()

    def _run_agent():
        return chat_agent_agent.run(agent_prompt)

    response_text = await loop.run_in_executor(None, _run_agent)

    return {"response": response_text, "bq_context_rows": len(bq_context) if bq_context else 0, "web_snippets": len(web_snippets) if web_snippets else 0}