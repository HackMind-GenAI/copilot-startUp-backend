from datetime import timedelta
import io
import json
import os
from fastapi import FastAPI, Request
from services.metrics_generator import generate_metrics
from services.devils_advocate import get_devils_advocate_analysis, DevilsAdvocateRequest, DevilsAdvocateResponse
from services.comparison_analysis import get_comparison_analysis, ComparisonRequest, ComparisonResponse
from langsmith import traceable
import uvicorn
from models.summarize import HelloRequest
from google.cloud import storage
import base64
from google.cloud import bigquery
import uuid
from datetime import datetime
import zipfile
import google.auth

bq_client = bigquery.Client()
table_id = os.environ.get("BQ_TABLE_ID")

app = FastAPI()

@traceable
@app.post("/analyze")
def main(userInput: HelloRequest):
    result=generate_metrics(userInput.name)
    return result

@traceable
@app.post("/getDevilsAdvocate", response_model=DevilsAdvocateResponse)
def get_devils_advocate(request: DevilsAdvocateRequest):
    """
    Devil's Advocate endpoint that provides critical analysis using LangChain Google agent
    """
    result = get_devils_advocate_analysis(request)
    return result

@traceable
@app.post("/getComparisonData", response_model=ComparisonResponse)
def get_comparison_data(request: ComparisonRequest):
    """
    Competitor Analysis endpoint that provides comprehensive market analysis using web search and LangChain agents
    """
    result = get_comparison_analysis(request)
    return result

try:
    storage_client = storage.Client()
except Exception as e:
    print(f"Warning: Google Cloud Storage client could not be initialized: {e}")
    storage_client = None

def download_gcs_blob(bucket_name, source_blob_name):
    """Downloads a blob from a GCS bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    return blob.download_as_bytes()


@app.post("/test-event")
async def handle_gcs_event(request: Request):
    event = await request.json()
    event_id = event["generation"]
    bucket_name = event["bucket"]
    zip_blob_name = event["name"]
    print(f'{event}')
    print(f'{bucket_name},{zip_blob_name}')
    #folder_prefix = file_path.rsplit('/', 1)[0] + '/'
    zip_bytes = download_gcs_blob(bucket_name, zip_blob_name)
    
    multimodal_content_parts = []

    # Unpack zip in memory
    try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                for file_name in zf.namelist():
                    if file_name.startswith("__MACOSX") or file_name.endswith(".DS_Store") or file_name.startswith("._"):
                        continue
                    if file_name.endswith("/"):  # skip directories
                        continue

                    print(f"🔎 Processing {file_name}")
                    file_bytes = zf.read(file_name)

                    if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                        base64_encoded_image = base64.b64encode(file_bytes).decode("utf-8")
                        multimodal_content_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_encoded_image}"
                            }
                        })

                    elif file_name.lower().endswith(".txt"):
                        multimodal_content_parts.append({
                            "type": "text",
                            "text": file_bytes.decode("utf-8")
                        })

                    elif file_name.lower().endswith((".mp4", ".mov", ".avi")):
                        base64_encoded_video = base64.b64encode(file_bytes).decode("utf-8")
                        multimodal_content_parts.append({
                            "type": "media",
                            "media_url": base64_encoded_video,
                            "mime_type": "video/mp4"
                        })

                    elif file_name.lower().endswith((".pdf", ".pptx")):
                        base64_encoded_file = base64.b64encode(file_bytes).decode("utf-8")
                        multimodal_content_parts.append({
                            "type": "media",
                            "data": base64_encoded_file,
                            "mime_type": "application/pdf" if file_name.endswith(".pdf")
                                       else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        })
    except zipfile.BadZipFile:
            print("❌ Uploaded file is not a valid ZIP archive")
            return {"error": "Invalid ZIP file"}

    
    user_prompt = "Evaluate this complete data"
    final_prompt_content = [{"type": "text", "text": user_prompt}] + multimodal_content_parts

    try:
            result =  generate_metrics(final_prompt_content)
            print("✅ LLM result received")
    except Exception as e:
            print(f"❌ Error in generate_metrics: {e}")
            return {f"error": "LLM processing failed {e}"}
    
    try:
         pitch_dict = result.dict() if hasattr(result, "dict") else result

    # Unique ID for deduplication (event_id or generation)
         unique_id = event_id  # or use f"{bucket}/{name}/{generation}"

         merge_query = f"""
    MERGE `{table_id}` T
    USING (
        SELECT @id AS id,
               @basicInfo AS basicInfo,
               @metrics AS metrics,
               @financials AS financials,
               @team AS team,
               @equity AS equity,
               @market AS market,
               @product AS product,
               @exit AS exit,
               @business AS business,
               @legal AS legal,
               @created_at AS created_at
    ) S
    ON T.id = S.id
    WHEN NOT MATCHED THEN
      INSERT (id, basicInfo, metrics, financials, team, equity, market, product, exit, business, legal, created_at)
      VALUES (S.id, S.basicInfo, S.metrics, S.financials, S.team, S.equity, S.market, S.product, S.exit, S.business, S.legal, S.created_at)
    """

    # Prepare query parameters
         job_config = bigquery.QueryJobConfig(
            query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING", unique_id),
            bigquery.ScalarQueryParameter("basicInfo", "STRING", json.dumps(pitch_dict.get("basicInfo", {}))),
            bigquery.ScalarQueryParameter("metrics", "STRING", json.dumps(pitch_dict.get("metrics", {}))),
            bigquery.ScalarQueryParameter("financials", "STRING", json.dumps(pitch_dict.get("financials", {}))),
            bigquery.ScalarQueryParameter("team", "STRING", json.dumps(pitch_dict.get("team", []))),
            bigquery.ScalarQueryParameter("equity", "STRING", json.dumps(pitch_dict.get("equity", {}))),
            bigquery.ScalarQueryParameter("market", "STRING", json.dumps(pitch_dict.get("market", {}))),
            bigquery.ScalarQueryParameter("product", "STRING", json.dumps(pitch_dict.get("product", {}))),
            bigquery.ScalarQueryParameter("exit", "STRING", json.dumps(pitch_dict.get("exit", {}))),
            bigquery.ScalarQueryParameter("business", "STRING", json.dumps(pitch_dict.get("business", {}))),
            bigquery.ScalarQueryParameter("legal", "STRING", json.dumps(pitch_dict.get("legal", {}))),
            bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", datetime.utcnow())
        ]
    )

    # Execute MERGE query
         query_job = bq_client.query(merge_query, job_config=job_config)
         query_job.result()  # wait for completion

         print(f"✅ Row with ID={unique_id} inserted if it did not exist")

    except Exception as e:
         print(f"❌ Error inserting into BigQuery: {e}")

    return result



@app.get("/records")
async def get_filtered_records():
    try:
        query = f"""
        SELECT *
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY id ORDER BY created_at DESC) AS rn
            FROM `{table_id}`
            WHERE devils_advocate IS NOT NULL
              AND competitors IS NOT NULL
        ) t
        WHERE rn = 1
        ORDER BY created_at DESC
        """
        query_job = bq_client.query(query)
        results = query_job.result()
        records = [dict(row) for row in results]

        return {"count": len(records), "records": records}

    except Exception as e:
        return {"error": str(e)}
# if __name__ == "__main__":
#     uvicorn.run("main:app")




