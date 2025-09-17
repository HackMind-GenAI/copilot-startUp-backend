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

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

# Initialize web search with error handling
try:
    search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search_tool = DuckDuckGoSearchRun(api_wrapper=search_wrapper)
    search_available = True
except Exception as e:
    print(f"Web search not available: {e}")
    search_tool = None
    search_available = False

def create_industry_research_tool():
    """Tool for industry research and market analysis"""
    def research_industry(query: str) -> str:
        if not search_available or search_tool is None:
            # Fallback analysis using LLM knowledge
            response = llm.invoke([
                SystemMessage(content="""You are a senior industry analyst with extensive knowledge of various industries. 
                Provide comprehensive industry analysis including market size estimates, key trends, growth drivers, 
                competitive dynamics, and investment landscape based on your knowledge. Be specific with numbers where possible 
                and acknowledge when information might be estimated."""),
                HumanMessage(content=f"Provide detailed industry analysis for: {query}")
            ])
            return response.content
        
        try:
            search_query = f"{query} industry analysis market size trends 2024 2025"
            search_results = search_tool.run(search_query)
            
            # Use LLM to analyze and synthesize the search results
            response = llm.invoke([
                SystemMessage(content="You are an industry analyst. Analyze the search results and provide a comprehensive industry overview including market size, trends, and key insights. Focus on factual information and recent data."),
                HumanMessage(content=f"Analyze this industry data and provide insights: {search_results}")
            ])
            return response.content
        except Exception as e:
            # Fallback to LLM knowledge if search fails
            response = llm.invoke([
                SystemMessage(content="""You are a senior industry analyst with extensive knowledge of various industries. 
                Provide comprehensive industry analysis including market size estimates, key trends, growth drivers, 
                competitive dynamics, and investment landscape based on your knowledge. Be specific with numbers where possible 
                and acknowledge when information might be estimated."""),
                HumanMessage(content=f"Web search failed, provide analysis based on knowledge for: {query}")
            ])
            return response.content
    
    return Tool(
        name="industry_research",
        description="Researches industry trends, market size, and competitive landscape",
        func=research_industry
    )

def create_competitor_analysis_tool():
    """Tool for competitor analysis and valuation research"""
    def analyze_competitors(query: str) -> str:
        if not search_available or search_tool is None:
            # Fallback competitor analysis using LLM knowledge
            response = llm.invoke([
                SystemMessage(content="""You are a competitive intelligence analyst with deep knowledge of various industries. 
                Provide comprehensive competitor analysis including major players, their business models, valuations, 
                revenue estimates, funding history, competitive advantages, and market positioning. 
                Be specific with known data and clearly indicate when providing estimates."""),
                HumanMessage(content=f"Provide detailed competitor analysis for: {query}")
            ])
            return response.content
            
        try:
            search_query = f"{query} competitors valuation funding revenue profitability startups companies"
            search_results = search_tool.run(search_query)
            
            # Use LLM to extract competitor information
            response = llm.invoke([
                SystemMessage(content="""You are a competitive intelligence analyst. Extract and organize competitor information from search results. 
                Focus on: company names, valuations, revenue figures, funding rounds, profitability status, and key competitive advantages. 
                Format the information clearly and cite specific metrics when available."""),
                HumanMessage(content=f"Extract competitor data from these search results: {search_results}")
            ])
            return response.content
        except Exception as e:
            # Fallback to LLM knowledge if search fails
            response = llm.invoke([
                SystemMessage(content="""You are a competitive intelligence analyst with deep knowledge of various industries. 
                Provide comprehensive competitor analysis including major players, their business models, valuations, 
                revenue estimates, funding history, competitive advantages, and market positioning. 
                Be specific with known data and clearly indicate when providing estimates."""),
                HumanMessage(content=f"Web search failed, provide competitor analysis based on knowledge for: {query}")
            ])
            return response.content
    
    return Tool(
        name="competitor_analysis",
        description="Analyzes competitors, their valuations, revenue, and performance metrics",
        func=analyze_competitors
    )

def create_funding_landscape_tool():
    """Tool for investment and funding landscape research"""
    def research_funding(query: str) -> str:
        if not search_available or search_tool is None:
            # Fallback funding analysis using LLM knowledge
            response = llm.invoke([
                SystemMessage(content="""You are an investment analyst with extensive knowledge of funding patterns across various industries. 
                Provide comprehensive analysis of the funding landscape including typical valuation ranges, active investors, 
                funding stage patterns, recent trends, and investment criteria. Be specific with known data and indicate estimates."""),
                HumanMessage(content=f"Provide detailed funding landscape analysis for: {query}")
            ])
            return response.content
            
        try:
            search_query = f"{query} startup funding investment rounds venture capital valuation 2024"
            search_results = search_tool.run(search_query)
            
            # Use LLM to analyze funding trends
            response = llm.invoke([
                SystemMessage(content="You are an investment analyst. Analyze funding patterns, investment trends, and valuation multiples in this industry. Focus on recent funding rounds, investor preferences, and market conditions."),
                HumanMessage(content=f"Analyze the funding landscape from this data: {search_results}")
            ])
            return response.content
        except Exception as e:
            # Fallback to LLM knowledge if search fails
            response = llm.invoke([
                SystemMessage(content="""You are an investment analyst with extensive knowledge of funding patterns across various industries. 
                Provide comprehensive analysis of the funding landscape including typical valuation ranges, active investors, 
                funding stage patterns, recent trends, and investment criteria. Be specific with known data and indicate estimates."""),
                HumanMessage(content=f"Web search failed, provide funding analysis based on knowledge for: {query}")
            ])
            return response.content
    
    return Tool(
        name="funding_research",
        description="Researches funding trends, investment patterns, and valuation benchmarks",
        func=research_funding
    )

def create_market_trends_tool():
    """Tool for market trends and growth analysis"""
    def analyze_market_trends(query: str) -> str:
        if not search_available or search_tool is None:
            # Fallback market trends analysis using LLM knowledge
            response = llm.invoke([
                SystemMessage(content="""You are a market research analyst with deep knowledge of market trends across industries. 
                Provide comprehensive market trend analysis including growth drivers, emerging technologies, consumer behavior shifts, 
                regulatory changes, and future opportunities. Be specific with trends and acknowledge timeframes."""),
                HumanMessage(content=f"Provide detailed market trends analysis for: {query}")
            ])
            return response.content
            
        try:
            search_query = f"{query} market trends growth forecast disruption innovation 2024 2025"
            search_results = search_tool.run(search_query)
            
            # Use LLM to analyze market trends
            response = llm.invoke([
                SystemMessage(content="You are a market research analyst. Identify key market trends, growth drivers, disruptions, and future opportunities. Focus on actionable insights for investors and entrepreneurs."),
                HumanMessage(content=f"Analyze market trends from this data: {search_results}")
            ])
            return response.content
        except Exception as e:
            # Fallback to LLM knowledge if search fails
            response = llm.invoke([
                SystemMessage(content="""You are a market research analyst with deep knowledge of market trends across industries. 
                Provide comprehensive market trend analysis including growth drivers, emerging technologies, consumer behavior shifts, 
                regulatory changes, and future opportunities. Be specific with trends and acknowledge timeframes."""),
                HumanMessage(content=f"Web search failed, provide market trends analysis based on knowledge for: {query}")
            ])
            return response.content
    
    return Tool(
        name="market_trends",
        description="Analyzes market trends, growth patterns, and future opportunities",
        func=analyze_market_trends
    )

# Create tools
industry_tool = create_industry_research_tool()
competitor_tool = create_competitor_analysis_tool()
funding_tool = create_funding_landscape_tool()
trends_tool = create_market_trends_tool()

# Initialize memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create the comparison agent
comparison_agent = initialize_agent(
    tools=[industry_tool, competitor_tool, funding_tool, trends_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

@traceable
def get_comparison_analysis(request: ComparisonRequest) -> ComparisonResponse:
    """
    Generate comprehensive competitor and market analysis using web search and LangChain agents
    """
    try:
        # Prepare the search context
        search_context = f"Company: {request.company_name}, Industry: {request.industry}"
        if request.business_model:
            search_context += f", Business Model: {request.business_model}"
        if request.location:
            search_context += f", Location: {request.location}"
        if request.target_market:
            search_context += f", Target Market: {request.target_market}"

        # Get industry overview
        print("Researching industry overview...")
        industry_overview = industry_tool.func(f"{request.industry} {request.business_model}")
        
        # Get competitor analysis
        print("Analyzing competitors...")
        competitor_analysis = competitor_tool.func(f"{request.industry} {request.company_name} competitors")
        
        # Get funding landscape
        print("Researching funding landscape...")
        funding_landscape = funding_tool.func(f"{request.industry} startup funding")
        
        # Get market trends
        print("Analyzing market trends...")
        market_trends = trends_tool.func(f"{request.industry} market trends")
        
        # Generate comprehensive analysis using the agent
        agent_prompt = f"""
        You are a senior investment analyst conducting due diligence for a potential investment in {request.company_name} 
        in the {request.industry} industry. Using the research data provided, create a comprehensive competitive analysis 
        that includes:
        
        1. Industry overview and market size
        2. Key competitor analysis with specific metrics
        3. Market trends and growth opportunities
        4. Investment landscape and funding patterns
        5. Benchmarking insights and recommendations
        
        Research Data:
        - Industry Analysis: {industry_overview}
        - Competitor Analysis: {competitor_analysis}  
        - Funding Landscape: {funding_landscape}
        - Market Trends: {market_trends}
        
        Provide actionable insights for investors considering this space.
        """
        
        # Run the agent for comprehensive analysis
        comprehensive_analysis = comparison_agent.run(agent_prompt)
        
        # Parse competitor data (simplified - in production you'd want more sophisticated parsing)
        # For now, we'll extract key competitors from the analysis
        competitors_data = []
        try:
            # This is a simplified extraction - you might want to use more sophisticated parsing
            if "competitors" in competitor_analysis.lower():
                # Extract competitor names and basic info
                competitor_lines = competitor_analysis.split('\n')
                for line in competitor_lines:
                    if any(keyword in line.lower() for keyword in ['valuation', 'revenue', 'funding']):
                        # Extract basic competitor info (this is simplified)
                        competitors_data.append(CompetitorData(
                            name="Competitor Analysis Available",
                            valuation="See detailed analysis",
                            revenue="See detailed analysis", 
                            profitability_status="See detailed analysis",
                            funding_rounds="See detailed analysis",
                            key_metrics="See detailed analysis",
                            competitive_advantages="See detailed analysis"
                        ))
                        break
        except Exception:
            pass
        
        # If no specific competitor data extracted, provide placeholder
        if not competitors_data:
            competitors_data = [CompetitorData(
                name="Comprehensive competitor data",
                valuation="Available in detailed analysis below",
                revenue="Available in detailed analysis below",
                profitability_status="Available in detailed analysis below", 
                funding_rounds="Available in detailed analysis below",
                key_metrics="Available in detailed analysis below",
                competitive_advantages="Available in detailed analysis below"
            )]
        
        return ComparisonResponse(
            industry_overview=industry_overview,
            market_size="Detailed in industry overview above",
            key_competitors=competitors_data,
            market_trends=market_trends,
            investment_landscape=funding_landscape,
            benchmarking_insights=competitor_analysis,
            recommendations=comprehensive_analysis
        )
        
    except Exception as e:
        print(f"Error in comparison analysis: {str(e)}")
        return ComparisonResponse(
            industry_overview=f"Error generating industry overview: {str(e)}",
            market_size="Unable to determine market size",
            key_competitors=[],
            market_trends=f"Error analyzing market trends: {str(e)}",
            investment_landscape=f"Error researching investment landscape: {str(e)}",
            benchmarking_insights=f"Error generating benchmarking insights: {str(e)}",
            recommendations=f"Error generating recommendations: {str(e)}"
        )
