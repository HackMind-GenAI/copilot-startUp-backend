import json
from fastapi import FastAPI, Request
from services.metrics_generator import generate_metrics
from langsmith import traceable
import uvicorn
from models.summarize import HelloResponse,HelloRequest
from google.cloud import storage
import base64

app = FastAPI()
@traceable
@app.post("/analyze")
def main(userInput: HelloRequest):
    result=generate_metrics(userInput.name)
    return result

storage_client = storage.Client()

def download_gcs_blob(bucket_name, source_blob_name):
    """Downloads a blob from a GCS bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    return blob.download_as_bytes()


@app.post("/test-event")
async def handle_gcs_event(request: Request):
    event = await request.json()
    print("Received Eventarc event:", json.dumps(event, indent=2))

    bucket_name = event["bucket"]
    file_path = event["name"]
    folder_prefix = file_path.rsplit('/', 1)[0] + '/'

    multimodal_content_parts = []
    # List and process all files in the folder
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_prefix)

    for blob in blobs:
        if blob.name.endswith('/'):
            continue

        file_bytes = blob.download_as_bytes()
        
        # Prepare content based on file type
        if blob.content_type.startswith("image/"):
            base64_encoded_image = base64.b64encode(file_bytes).decode('utf-8')
            multimodal_content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{blob.content_type};base64,{base64_encoded_image}"}
            })
        elif blob.content_type.startswith("text/"):
            multimodal_content_parts.append({
                "type": "text",
                "text": file_bytes.decode('utf-8')
            })
        elif blob.content_type.startswith("video/"):
            multimodal_content_parts.append({
                "type": "video_url",
                "video_url": {"url": f"gs://{bucket_name}/{blob.name}"}
            })
        elif blob.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
            file_data = io.BytesIO(file_bytes)
            multimodal_content_parts.append({
                "type": "file_url",
                "url": "data:application/octet-stream;base64," + base64.b64encode(file_data.read()).decode('utf-8')
            })

    # Add the user prompt to the list of content parts
    user_prompt = "Based on the contents of the entire folder, provide a summary and key insights. The folder may contain documents, images, and videos. Respond in the structured JSON format."
    final_prompt_content = [{"type": "text", "text": user_prompt}] + multimodal_content_parts


    # 👉 Call your existing logic here
    res = f"New file {file_path} uploaded in bucket {bucket_name},{folder_prefix}"
    print(res)

    result=generate_metrics(final_prompt_content)
    return result

# if __name__ == "__main__":
#     uvicorn.run("main:app")




