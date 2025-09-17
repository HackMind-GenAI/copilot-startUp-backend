from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import dotenv
from langsmith import traceable
from models.summarize import HelloRequest,HelloResponse
dotenv.load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash").with_structured_output(HelloResponse)
@traceable
def generate_metrics(input:str):
    response = llm.invoke([
        SystemMessage(content="You are a startUp Analyst. Given the input, you generate a metrics and evaluatioin criteriua and help founders to evaluate a startUp to invest in it."), 
        HumanMessage(content=input)])
    print(response)
    return response
    

