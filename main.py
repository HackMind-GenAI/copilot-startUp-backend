import json
from fastapi import FastAPI, Request
from services.metrics_generator import generate_metrics
from langsmith import traceable
import uvicorn
from models.summarize import HelloResponse,HelloRequest

app = FastAPI()
@traceable
@app.post("/analyze")
def main(userInput: HelloRequest):
    result=generate_metrics(userInput.name)
    return result


@app.post("/test-event")
async def handle_gcs_event(request: Request):
    event = await request.json()
    print("Received Eventarc event:", json.dumps(event, indent=2))

    bucket = event["bucket"]
    file_name = event["name"]

    # 👉 Call your existing logic here
    result = f"New file {file_name} uploaded in bucket {bucket}"
    print(result)

    return {"message": result}

# if __name__ == "__main__":
#     uvicorn.run("main:app")




