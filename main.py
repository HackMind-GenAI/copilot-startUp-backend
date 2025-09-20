from datetime import timedelta
import io
import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from services.metrics_generator import generate_metrics
from services.devils_advocate import get_devils_advocate_analysis, DevilsAdvocateRequest, DevilsAdvocateResponse
from services.comparison_analysis import get_competitor_analysis, CompanyData, CompetitorResponse
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
from models.chat import ChatRequest, ChatResponse
from services.chat_agent import run_chat_agent
# Use BigQuery client directly; initialize lazily and safely
bq_client = None
try:
    bq_client = bigquery.Client()
except Exception as e:
    print(f"Warning: BigQuery client could not be initialized at startup: {e}")
    bq_client = None

table_id = os.environ.get("BQ_TABLE_ID")

# Environment: enable docs only for development-like environments
# Recognize `ENV` or `APP_ENV` (fallback to 'development')
ENV = os.getenv("ENV", os.getenv("APP_ENV", "development")).lower()
is_dev = ENV in ("dev", "development", "local")
# Auto-open docs only when requested (and only in dev)
AUTO_OPEN_SWAGGER = os.getenv("AUTO_OPEN_SWAGGER", "true").lower() in ("1", "true", "yes")

# Configure FastAPI docs visibility based on environment
if is_dev:
    _docs_url = "/docs"
    _redoc_url = "/redoc"
    _openapi_url = "/openapi.json"
else:
    _docs_url = None
    _redoc_url = None
    _openapi_url = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to run startup/shutdown events.

    Auto-opens the Swagger UI in the browser on startup (dev convenience)
    only when running in a development-like environment and `AUTO_OPEN_SWAGGER`
    is enabled.
    """
    if is_dev and AUTO_OPEN_SWAGGER:
        def _open():
            # short delay so the server has time to bind the port
            time.sleep(1)
            port = os.getenv("PORT", "8000")
            host = os.getenv("HOST", "127.0.0.1")
            url = f"http://{host}:{port}/docs"
            try:
                webbrowser.open(url)
                print(f"Opened Swagger UI at {url}")
            except Exception as e:
                print(f"Could not open browser for Swagger UI: {e}")

        t = threading.Thread(target=_open, daemon=True)
        t.start()

    yield


app = FastAPI(
    title="HackMind StartUp Backend",
    description="APIs for startup analysis: metrics, devil's-advocate, comparison, record queries and chat agent.",
    version="0.1.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=lifespan,
)


if _docs_url:
    @app.get("/", include_in_schema=False)
    def docs_redirect():
        """Redirect root URL to the Swagger UI"""
        return RedirectResponse(url=_docs_url)

@traceable
@app.post("/analyze", tags=["Metrics"], summary="Generate metrics from input")
def main(userInput: HelloRequest):
    result=generate_metrics(userInput.name)
    return result

@traceable
@app.post("/getDevilsAdvocate", response_model=DevilsAdvocateResponse, tags=["Devil's Advocate"], summary="Devil's Advocate analysis")
def get_devils_advocate(request: DevilsAdvocateRequest):
    """
    Devil's Advocate endpoint that provides critical analysis using LangChain Google agent
    """
    result = get_devils_advocate_analysis(request)
    return result

@traceable
@app.post("/getComparisonData", response_model=ComparisonResponse, tags=["Comparison"], summary="Competitor / market comparison")
def get_comparison_data(request: ComparisonRequest):
    """
    Enhanced Competitor Analysis endpoint that provides comprehensive competitive intelligence
    using the company's data and web search with LangChain agents
    """
    result = get_competitor_analysis(company_data)
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


@app.post("/test-event", tags=["GCS"], summary="Handle GCS test event (zip processing)")
async def handle_gcs_event(request: Request):
    global bq_client
    event = await request.json()
    event_id = event["id"]
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
            row_id = str(uuid.uuid4())
            row = {
        "id": event_id,  # unique id
        "basicInfo": json.dumps(pitch_dict.get("basicInfo", {})),
        "metrics": json.dumps(pitch_dict.get("metrics", {})),
        "financials": json.dumps(pitch_dict.get("financials", {})),
        "team": json.dumps(pitch_dict.get("team", [])),
        "equity": json.dumps(pitch_dict.get("equity", {})),
        "market": json.dumps(pitch_dict.get("market", {})),
        "product": json.dumps(pitch_dict.get("product", {})),
        "exit": json.dumps(pitch_dict.get("exit", {})),
        "legal": json.dumps(pitch_dict.get("legal", {})),
        "investment_summary": json.dumps(pitch_dict.get("investment_summary", {})),
        "created_at": datetime.utcnow().isoformat()
    }
            if bq_client is None:
                # Try to initialize on demand; if it fails, log and skip insertion
                try:
                    bq_client = bigquery.Client()
                except Exception as e:
                    print(f"Warning: BigQuery client initialization failed during insert: {e}")
                    bq_client = None

            if bq_client:
                errors = bq_client.insert_rows_json(table_id, [row])
                if errors:
                    print(f"❌ BigQuery insert errors: {errors}")
                else:
                    print(f"✅ Inserted into BigQuery with ID: {row_id}")
            else:
                print("⚠️ Skipping BigQuery insert because client is unavailable")
    except Exception as e:
            print(f"❌ Error inserting into BigQuery: {e}")
    return result


@app.get("/records", tags=["Records"], summary="Get filtered records (latest per id)")
async def get_filtered_records():
    global bq_client
    try:
        if bq_client is None:
            try:
                bq_client = bigquery.Client()
            except Exception as e:
                return {"error": f"BigQuery client unavailable: {e}"}
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

  
@app.post("/chat", response_model=ChatResponse, tags=["Chat"], summary="Chat agent endpoint")
async def chat_agent(request: ChatRequest):
    """Chat endpoint that forwards the user's message to the chat agent business logic.

    Expects a `ChatRequest` body and returns `ChatResponse`.
    """
    user_message = request.message
    if not user_message:
        return ChatResponse(reply="Error: No message provided")

    try:
        # Do not accept raw SQL from external requests; allow selecting a named query_type
        query_type = request.query_type if hasattr(request, "query_type") else None
        startup_id = request.startup_id if hasattr(request, "startup_id") else None
        history = request.history if hasattr(request, "history") else None
        result = await run_chat_agent(user_message, history=history, query_type=query_type, startup_id=startup_id)
        response_obj = result.get("response") if isinstance(result, dict) else result

        # Try common attributes first, otherwise stringify the object
        if hasattr(response_obj, "content"):
            reply = str(response_obj.content)
        elif hasattr(response_obj, "text"):
            reply = str(response_obj.text)
        else:
            reply = str(response_obj)

        return ChatResponse(reply=reply)
    except Exception as e:
        return ChatResponse(reply=f"Error: {e}")


#if __name__ == "__main__":
#    uvicorn.run("main:app")




