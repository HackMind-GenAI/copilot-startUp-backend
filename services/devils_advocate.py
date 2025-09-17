from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
import dotenv
from langsmith import traceable
from pydantic import BaseModel

dotenv.load_dotenv()

class DevilsAdvocateRequest(BaseModel):
    message: str
    startup_idea: str = None

class DevilsAdvocateResponse(BaseModel):
    counter_argument: str
    risk_assessment: str
    alternative_perspective: str

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

def create_counter_argument_tool():
    """Tool to generate counter-arguments"""
    def counter_argue(input_text: str) -> str:
        response = llm.invoke([
            SystemMessage(content="You are a critical thinker who provides counter-arguments. Challenge the given statement with logical reasoning and evidence-based concerns."),
            HumanMessage(content=f"Provide a counter-argument to: {input_text}")
        ])
        return response.content
    
    return Tool(
        name="counter_argument",
        description="Generates counter-arguments to challenge a given statement or idea",
        func=counter_argue
    )

def create_risk_assessment_tool():
    """Tool to assess risks"""
    def assess_risks(input_text: str) -> str:
        response = llm.invoke([
            SystemMessage(content="You are a risk analyst. Identify potential risks, challenges, and negative outcomes for the given scenario."),
            HumanMessage(content=f"Analyze the risks for: {input_text}")
        ])
        return response.content
    
    return Tool(
        name="risk_assessment",
        description="Analyzes potential risks and challenges",
        func=assess_risks
    )

def create_alternative_perspective_tool():
    """Tool to provide alternative perspectives"""
    def alternative_view(input_text: str) -> str:
        response = llm.invoke([
            SystemMessage(content="You are a creative thinker who provides alternative perspectives. Consider different viewpoints, market conditions, and scenarios."),
            HumanMessage(content=f"Provide alternative perspectives on: {input_text}")
        ])
        return response.content
    
    return Tool(
        name="alternative_perspective",
        description="Provides alternative viewpoints and perspectives",
        func=alternative_view
    )

# Create tools
counter_argument_tool = create_counter_argument_tool()
risk_assessment_tool = create_risk_assessment_tool()
alternative_perspective_tool = create_alternative_perspective_tool()

# Initialize memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create the Devil's Advocate agent
devils_advocate_agent = initialize_agent(
    tools=[counter_argument_tool, risk_assessment_tool, alternative_perspective_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

@traceable
def get_devils_advocate_analysis(request: DevilsAdvocateRequest) -> DevilsAdvocateResponse:
    """
    Generate a Devil's Advocate analysis using LangChain agent
    """
    try:
        # Prepare the input message
        if request.startup_idea:
            input_message = f"Startup Idea: {request.startup_idea}\nMessage: {request.message}"
        else:
            input_message = request.message

        # System prompt for the agent
        agent_prompt = f"""
        You are a Devil's Advocate AI agent specializing in startup analysis. Your role is to critically examine ideas, 
        identify potential flaws, and challenge assumptions. For the following input, use your tools to:
        
        1. Generate thoughtful counter-arguments
        2. Assess potential risks and challenges
        3. Provide alternative perspectives
        
        Input: {input_message}
        
        Provide a comprehensive analysis that helps entrepreneurs think critically about their ideas.
        """

        # Run the agent
        result = devils_advocate_agent.run(agent_prompt)
        
        # Parse the result and structure the response
        # For now, we'll use the full result as counter_argument and generate specific responses
        counter_arg_result = counter_argument_tool.func(input_message)
        risk_result = risk_assessment_tool.func(input_message)
        alternative_result = alternative_perspective_tool.func(input_message)
        
        return DevilsAdvocateResponse(
            counter_argument=counter_arg_result,
            risk_assessment=risk_result,
            alternative_perspective=alternative_result
        )
        
    except Exception as e:
        print(f"Error in Devil's Advocate analysis: {str(e)}")
        return DevilsAdvocateResponse(
            counter_argument="Error generating counter-argument",
            risk_assessment="Error assessing risks",
            alternative_perspective="Error providing alternative perspective"
        )