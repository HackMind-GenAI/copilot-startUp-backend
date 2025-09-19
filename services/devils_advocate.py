from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
import dotenv
from langsmith import traceable
from pydantic import BaseModel
import re

dotenv.load_dotenv()

# ------------------ Request & Response Models ------------------
class DevilsAdvocateRequest(BaseModel):
    message: str
    startup_idea: str = None

class DevilsAdvocateResponse(BaseModel):
    counter_argument: str
    risk_assessment: str
    alternative_perspective: str
    data_consistency: str
    evidence_strength: str
    improvements: str
    overall_suggestion: str

# ------------------ LLM Setup ------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# ------------------ Tool Definitions ------------------
def create_tool(name, system_role, description, task):
    """Utility to create tools dynamically"""
    def tool_func(input_text: str) -> str:
        response = llm.invoke([
            SystemMessage(content=system_role),
            HumanMessage(content=f"{task}: {input_text}")
        ])
        return response.content
    return Tool(name=name, description=description, func=tool_func)

# Existing tools
counter_argument_tool = create_tool(
    "counter_argument",
    "You are a critical thinker who provides counter-arguments.",
    "Generates counter-arguments to challenge a given statement or idea",
    "Provide a counter-argument to"
)

risk_assessment_tool = create_tool(
    "risk_assessment",
    "You are a risk analyst. Identify potential risks, challenges, and negative outcomes.",
    "Analyzes potential risks and challenges",
    "Analyze the risks for"
)

alternative_perspective_tool = create_tool(
    "alternative_perspective",
    "You are a creative thinker who provides alternative perspectives.",
    "Provides alternative viewpoints and perspectives",
    "Provide alternative perspectives on"
)

# New tools
data_consistency_tool = create_tool(
    "data_consistency",
    "You are a data auditor. Check for contradictions, missing details, or logical gaps.",
    "Checks consistency and gaps in the data",
    "Check data consistency for"
)

evidence_strength_tool = create_tool(
    "evidence_strength",
    "You are an evidence evaluator. Judge if the claims/data are strong, weak, or unsupported.",
    "Evaluates strength of provided evidence",
    "Evaluate the strength of evidence for"
)

improvements_tool = create_tool(
    "improvements",
    "You are a mentor. Suggest actionable improvements and refinements to the idea.",
    "Suggests improvements and next steps",
    "Suggest improvements for"
)

# ------------------ Tools + Agent ------------------
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

devils_advocate_agent = initialize_agent(
    tools=[
        counter_argument_tool,
        risk_assessment_tool,
        alternative_perspective_tool,
        data_consistency_tool,
        evidence_strength_tool,
        improvements_tool
    ],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# ------------------ Parser ------------------
def parse_agent_output(output: str) -> DevilsAdvocateResponse:
    """
    Parse structured agent output into DevilsAdvocateResponse.
    """
    def extract(section: str) -> str:
        pattern = rf"\*\*{section}\*\*:(.*?)(?=\n- \*\*|$)"
        match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "Not found"

    return DevilsAdvocateResponse(
        counter_argument=extract("Counter-Arguments"),
        risk_assessment=extract("Risk Assessment"),
        alternative_perspective=extract("Alternative Perspectives"),
        data_consistency=extract("Data Consistency Check"),
        evidence_strength=extract("Evidence Strength"),
        improvements=extract("Improvements"),
        overall_suggestion=extract("Overall Suggestion")
    )

# ------------------ Main Function ------------------
@traceable
def get_devils_advocate_analysis(request: DevilsAdvocateRequest) -> DevilsAdvocateResponse:
    """
    Generate a Devil's Advocate analysis using LangChain agent.
    Now includes counter-arguments, risks, alternatives, evidence strength, data consistency, improvements, and overall suggestion.
    """
    try:
        # Prepare the input message
        if request.startup_idea:
            input_message = f"Startup Idea: {request.startup_idea}\nMessage: {request.message}"
        else:
            input_message = request.message

        # Enhanced system prompt
        agent_prompt = f"""
        You are "Devil’s Advocate", an AI startup analyst that uses available tools 
        (counter_argument, risk_assessment, alternative_perspective, data_consistency, evidence_strength, improvements) 
        to rigorously test assumptions and challenge input data or ideas.

        ### Instructions
        - For every input, first restate it clearly.
        - Use your tools to:
          1. Generate counter-arguments
          2. Identify risks and weaknesses
          3. Provide alternative perspectives
          4. Check data consistency and gaps
          5. Judge the strength of evidence
          6. Suggest improvements and refinements
        - After using the tools, synthesize everything into a **final structured response**.

        ### Final Output Format
        - **Restated Input**: …
        - **Counter-Arguments**: …
        - **Risk Assessment**: …
        - **Alternative Perspectives**: …
        - **Data Consistency Check**: …
        - **Evidence Strength**: …
        - **Improvements**: …
        - **Overall Suggestion**: …

        ### Important
        - Always call the tools before producing the final response.
        - Ensure the final suggestion is balanced: critical but constructive.
        - Merge and summarize tool outputs neatly.

        Now analyze the following input:
        {input_message}
        """

        # Run the agent — it will call tools automatically
        result = devils_advocate_agent.run(agent_prompt)

        # Parse into structured response
        return parse_agent_output(result)

    except Exception as e:
        print(f"Error in Devil's Advocate analysis: {str(e)}")
        return DevilsAdvocateResponse(
            counter_argument="Error",
            risk_assessment="Error",
            alternative_perspective="Error",
            data_consistency="Error",
            evidence_strength="Error",
            improvements="Error",
            overall_suggestion="Error"
        )
