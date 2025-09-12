from fastapi import FastAPI
from services.metrics_generator import generate_metrics
from langsmith import traceable

from models.summarize import HelloResponse,HelloRequest

app = FastAPI()
@traceable
@app.post("/summarize")
def main(userInput: HelloRequest):
    result=generate_metrics(userInput.name)
    return result
