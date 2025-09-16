from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import dotenv
from langsmith import traceable
from models.founder_summary import FounderSummaryResponse
dotenv.load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash").with_structured_output(FounderSummaryResponse)
@traceable
def generate_oracle(input:str):
    response = llm.invoke([
        SystemMessage(content="You are a Startup Founder Analyst. Given the data of multiple startup founders, like their interview transcripts, news article etc, you generate a comprehensive profile summary about the asked founder, highlighting their strengths, weaknesses, their relation with other founders, and unique qualities. This summary will help investors and stakeholders understand the founder's potential and make informed decisions."), 
        HumanMessage(content=input)])
    print(response)
    return response
    

