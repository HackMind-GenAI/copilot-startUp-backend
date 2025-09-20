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

from typing import Optional, List, Dict, Any
import os
import json
import dotenv
import asyncio
import re

from google.cloud import bigquery
import requests

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory

dotenv.load_dotenv()

# Configuration
GOOGLE_GENAI_MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
print(f"Chat agent config: model={GOOGLE_GENAI_MODEL}")


# instantiate module-level LLM used by tools/agent
llm = ChatGoogleGenerativeAI(model=GOOGLE_GENAI_MODEL, temperature=0.2)

# Default BigQuery SQL (hard-coded in code; uses `BQ_TABLE_ID` env var)
TABLE_ID = os.getenv("BQ_TABLE_ID")
STARTUP_PITCH_TABLE_ID = os.getenv("BQ_TABLE_STARTUP_PITCH_ID")
if TABLE_ID:
    DEFAULT_BQ_SQL = f"""
    SELECT *
    FROM (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY created_at DESC) AS rn
      FROM `{TABLE_ID}`
      WHERE devils_advocate IS NOT NULL
        AND competitors IS NOT NULL
    ) t
    WHERE rn = 1
    ORDER BY created_at DESC
    LIMIT 50
    """
else:
    DEFAULT_BQ_SQL = None


def fetch_bigquery(bq_sql: str, project: Optional[str] = None, max_rows: int = 100, query_params: Optional[dict] = None) -> List[dict]:
    """Run a BigQuery SQL query and return rows as list of dicts.

    Requires `GOOGLE_APPLICATION_CREDENTIALS` env var or default application credentials.
    """
    client = bigquery.Client(project=project)
    job_config = None
    if query_params:
        params = [bigquery.ScalarQueryParameter(name, "STRING", value) for name, value in query_params.items()]
        job_config = bigquery.QueryJobConfig(query_parameters=params)
    query_job = client.query(bq_sql, job_config=job_config)
    results = query_job.result(max_results=max_rows)
    return [dict(row) for row in results]


# web search removed — agent will use BigQuery-provided context only


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
# web_search tool removed; this agent will rely on BigQuery context only


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
    tools=[bigquery_tool, summarize_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True,
)


async def run_chat_agent(user_query: str, history: Optional[List[Dict[str, Any]]] = None, query_type: Optional[str] = None, project: Optional[str] = None, startup_id: Optional[str] = None) -> dict:
    """Main entrypoint: fetch context, perform web search, call LLM and return the result.

    - `user_query`: user's question or instruction.
    - `bq_sql`: optional BigQuery SQL to run and include as context. If omitted, BQ step is skipped.
    - `project`: optional GCP project override for BigQuery client.
    """
    bq_context_deals = None
    bq_context_startups = None
    # web search removed — not used

    # Choose server-side hard-coded SQL based on `query_type` and optional `startup_id`
    use_sql = None
    # Validate startup_id if provided (simple alphanumeric + dashes/underscores)
    if startup_id:
        if not re.match(r"^[A-Za-z0-9_\-]{1,64}$", startup_id):
            raise ValueError("Invalid startup_id format")

    if startup_id and STARTUP_PITCH_TABLE_ID:
        # Parameterized query to fetch a specific startup by id
        use_sql = f"SELECT * FROM `{STARTUP_PITCH_TABLE_ID}` WHERE id = @startup_id LIMIT 50"
        startup_params = {"startup_id": startup_id}
    elif query_type == "startup_pitch" and STARTUP_PITCH_TABLE_ID:
        use_sql = f"SELECT * FROM `{STARTUP_PITCH_TABLE_ID}` LIMIT 50"
        startup_params = None
    else:
        use_sql = DEFAULT_BQ_SQL
        startup_params = None

    # Fetch both tables (deals and startup pitches) if available and include both previews
    loop = asyncio.get_running_loop()
    use_sql_deals = DEFAULT_BQ_SQL
    use_sql_startup = f"SELECT * FROM `{STARTUP_PITCH_TABLE_ID}` LIMIT 50" if STARTUP_PITCH_TABLE_ID else None

    # If a specific startup_id was requested, prefer fetching only that startup from the startup table
    if startup_id and STARTUP_PITCH_TABLE_ID:
        bq_context_startups = await loop.run_in_executor(None, fetch_bigquery, use_sql, project, 100, startup_params)
    else:
        if use_sql_deals:
            bq_context_deals = await loop.run_in_executor(None, fetch_bigquery, use_sql_deals, project)
        if use_sql_startup:
            bq_context_startups = await loop.run_in_executor(None, fetch_bigquery, use_sql_startup, project)

    # Prepare a safe, truncated JSON preview of the BigQuery results to include in the agent prompt
    bq_preview_deals = None
    bq_preview_startups = None
    if bq_context_deals:
        try:
            bq_preview_deals = json.dumps(bq_context_deals[:20], default=str)
        except Exception:
            bq_preview_deals = str(bq_context_deals)[:4000]
    if bq_context_startups:
        try:
            bq_preview_startups = json.dumps(bq_context_startups[:20], default=str)
        except Exception:
            bq_preview_startups = str(bq_context_startups)[:4000]

    # Incorporate structured chat history (if provided) for additional context
    history_text = None
    if history:
        items = []
        try:
            for h in history:
                if not h:
                    continue
                # accept either dicts with role/text or objects with attributes
                role = None
                text = None
                if isinstance(h, dict):
                    role = h.get("role")
                    text = h.get("text")
                else:
                    # fallback: try attribute access
                    role = getattr(h, "role", None)
                    text = getattr(h, "text", None)

                if role not in ("user", "assistant"):
                    # unknown role — treat as user
                    role = "user"

                if text is None:
                    continue

                items.append(f"- ({role}) {text}")

            history_text = "\n".join(items) if items else None
        except Exception:
            history_text = str(history)[:4000]

    # Build agent prompt instructing it to use tools when needed
    agent_prompt = f"""
You are a helpful startup analysis agent. You have access to tools: `bigquery_query` (executes SQL) and `summarize`.
Rules:
- Prefer using the provided BigQuery results included below rather than re-running the same query; only call `bigquery_query` if you need additional or different data.
- Use `summarize` to compress long contexts.
- Base your analysis on BigQuery context and the user's query (and provided chat history).

Chat history (oldest -> newest):
{history_text if history_text else 'None'}

User query: {user_query}

Selected query type: {query_type if query_type else 'default'}
If a BigQuery SQL was selected, here is the SQL (server-side):\n{use_sql if use_sql else 'None'}

If BigQuery results were fetched, truncated JSON previews are provided below (up to 20 rows each):
Deals table preview:
{bq_preview_deals if bq_preview_deals else 'None'}

Startup pitches table preview:
{bq_preview_startups if bq_preview_startups else 'None'}

Return a concise, actionable response and list which tools you used.
"""

    # Run the agent synchronously in a threadpool (initialize_agent returns a sync agent)
    loop = asyncio.get_running_loop()

    def _run_agent():
        return chat_agent_agent.run(agent_prompt)

    response_text = await loop.run_in_executor(None, _run_agent)

    return {
        "response": response_text,
        "bq_context_rows_deals": len(bq_context_deals) if bq_context_deals else 0,
        "bq_context_rows_startups": len(bq_context_startups) if bq_context_startups else 0,
    }