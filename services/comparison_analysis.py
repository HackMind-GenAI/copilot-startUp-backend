from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
import dotenv
from langsmith import traceable
from pydantic import BaseModel
from typing import List

dotenv.load_dotenv()

# ------------------ Models ------------------
class ComparisonRequest(BaseModel):
    company_name: str
    industry: str
    business_model: str = None
    location: str = None
    target_market: str = None

class CompetitorData(BaseModel):
    name: str
    valuation: str
    revenue: str
    profitability_status: str
    funding_rounds: str
    key_metrics: str
    competitive_advantages: str

class ComparisonResponse(BaseModel):
    industry_overview: str
    market_size: str
    key_competitors: List[CompetitorData]
    market_trends: str
    investment_landscape: str
    benchmarking_insights: str
    recommendations: str

# ------------------ LLM ------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

# ------------------ Search Setup ------------------
try:
    search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search_tool = DuckDuckGoSearchRun(api_wrapper=search_wrapper)
    search_available = True
except Exception as e:
    print(f"Web search not available: {e}")
    search_tool = None
    search_available = False

# ------------------ Tool Factory ------------------
def create_tool(name, system_role, description, query_template):
    def tool_func(query: str) -> str:
        if not search_available or search_tool is None:
            response = llm.invoke([
                SystemMessage(content=system_role),
                HumanMessage(content=f"{query_template}: {query}")
            ])
            return response.content
        try:
            search_results = search_tool.run(query)
            response = llm.invoke([
                SystemMessage(content=system_role),
                HumanMessage(content=f"Analyze this data: {search_results}")
            ])
            return response.content
        except Exception:
            response = llm.invoke([
                SystemMessage(content=system_role),
                HumanMessage(content=f"Web search failed, provide analysis from knowledge: {query}")
            ])
            return response.content
    return Tool(name=name, description=description, func=tool_func)

# ------------------ Tools ------------------
industry_tool = create_tool(
    "industry_research",
    "You are a senior industry analyst. Provide market size, dynamics, and growth factors.",
    "Researches industry trends and market size",
    "Industry analysis"
)

competitor_tool = create_tool(
    "competitor_analysis",
    "You are a competitive intelligence analyst. Extract valuations, revenue, funding, and competitive advantages of peers.",
    "Analyzes competitors and performance",
    "Competitor analysis"
)

funding_tool = create_tool(
    "funding_research",
    "You are an investment analyst. Provide funding patterns, active investors, and valuation benchmarks.",
    "Researches funding and investment landscape",
    "Funding analysis"
)

trends_tool = create_tool(
    "market_trends",
    "You are a market researcher. Identify trends, disruptions, and opportunities.",
    "Analyzes market trends and growth",
    "Market trends"
)

benchmarking_tool = create_tool(
    "benchmarking",
    "You are a benchmarking analyst. Compare company with peers across metrics like valuation, growth, profitability, and efficiency.",
    "Benchmarks performance vs competitors",
    "Benchmarking analysis"
)

swot_tool = create_tool(
    "swot_comparison",
    "You are a strategist. Provide SWOT comparison between company and key competitors.",
    "Provides SWOT analysis vs competitors",
    "SWOT comparison"
)

growth_tool = create_tool(
    "growth_trajectory",
    "You are a growth strategist. Compare growth trajectory (CAGR, market adoption, expansion pace) of company vs competitors.",
    "Analyzes growth trajectory vs peers",
    "Growth trajectory analysis"
)

# ------------------ Agent ------------------
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

comparison_agent = initialize_agent(
    tools=[industry_tool, competitor_tool, funding_tool, trends_tool,
           benchmarking_tool, swot_tool, growth_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# ------------------ Main Function ------------------
@traceable
def get_comparison_analysis(request: ComparisonRequest) -> ComparisonResponse:
    try:
        search_context = f"Company: {request.company_name}, Industry: {request.industry}"
        if request.business_model:
            search_context += f", Business Model: {request.business_model}"
        if request.location:
            search_context += f", Location: {request.location}"
        if request.target_market:
            search_context += f", Target Market: {request.target_market}"

        agent_prompt = f"""
        You are a senior investment analyst preparing a comparative analysis of {request.company_name} 
        in the {request.industry} industry.

        Use the available tools (industry_research, competitor_analysis, funding_research, market_trends,
        benchmarking, swot_comparison, growth_trajectory) to build a **comprehensive structured output**.

        ### Output Format
        - **Industry Overview**: …
        - **Market Size**: …
        - **Key Competitors**: (name, valuation, revenue, funding, profitability, advantages)
        - **Market Trends**: …
        - **Investment Landscape**: …
        - **Benchmarking Insights**: …
        - **Recommendations**: …

        Focus on comparing {request.company_name} with other companies in the same niche.
        Highlight who is growing faster, who has stronger metrics, and where {request.company_name} can improve.
        """

        result = comparison_agent.run(agent_prompt)

        # For simplicity, package results into response (structured parsing can be added like regex split)
        competitors_placeholder = [CompetitorData(
            name="See detailed analysis",
            valuation="Available in competitor analysis",
            revenue="Available in competitor analysis",
            profitability_status="Available in competitor analysis",
            funding_rounds="Available in competitor analysis",
            key_metrics="Available in competitor analysis",
            competitive_advantages="Available in competitor analysis"
        )]

        return ComparisonResponse(
            industry_overview=result,
            market_size="See industry section",
            key_competitors=competitors_placeholder,
            market_trends=result,
            investment_landscape=result,
            benchmarking_insights=result,
            recommendations=result
        )
    except Exception as e:
        print(f"Error in comparison analysis: {str(e)}")
        return ComparisonResponse(
            industry_overview="Error",
            market_size="Error",
            key_competitors=[],
            market_trends="Error",
            investment_landscape="Error",
            benchmarking_insights="Error",
            recommendations=f"Error: {str(e)}"
        )
