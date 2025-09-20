from datetime import timedelta
import io
import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from services.metrics_generator import generate_metrics

from services.founder_summary_generator import generate_oracle
from langsmith import traceable
import uvicorn
from models.summarize import HelloRequest
from models.founder_summary import FounderSummaryRequest

from services.devils_advocate import get_devils_advocate_analysis, DevilsAdvocateRequest, DevilsAdvocateResponse
from services.comparison_analysis import get_competitor_analysis, CompanyData, CompetitorResponse

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

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
@app.post("/getComparisonData", response_model=CompetitorResponse, tags=["Comparison"], summary="Competitor / market comparison")
def get_comparison_data(request: CompanyData):
    """
    Enhanced Competitor Analysis endpoint that provides comprehensive competitive intelligence
    using the company's data and web search with LangChain agents
    """
    result = get_competitor_analysis(request)
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

@traceable
@app.post("/test-event", tags=["GCS"], summary="Handle GCS test event (zip processing)")
async def handle_gcs_event(request: Request):
    global bq_client
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

@app.post("/founder-summary")
async def founder_summary(founder_request: FounderSummaryRequest):
    try:
        FOUNDER_PROFILING_TABLE_ID = os.getenv("BQ_TABLE_FOUNDER_PROFILE_ID")
        print("Received founder summary request:", founder_request.founder)

        # --- Start of BigQuery Integration ---

        # 1. Instantiate the BigQuery Client
        # The client will use the default credentials configured in your environment.
        client = bigquery.Client()

        # 2. Define the SQL query
        query = f"""
            SELECT *
            FROM `{FOUNDER_PROFILING_TABLE_ID}`
            LIMIT 1000
        """

        # 3. Execute the query and fetch results into a pandas DataFrame
        query_job = client.query(query)  # API request
        founders_df = query_job.to_dataframe() # Waits for the job to complete

        # 4. Convert the DataFrame to a string to be used in the prompt
        founders_data = founders_df.to_string()

        # --- End of BigQuery Integration ---

        multimodal_content_parts = []
        multimodal_content_parts.append({
            "type": "text",
            "text": founders_data
        })

        user_prompt = f"""Based on the provided founder profiles and documents, analyze {founder_request.founder}. Generate detailed report mentioned in the system prompt. Avoid one word answer, give reasoning for each field."""

        final_prompt_content = [{"type": "text", "text": user_prompt}] + multimodal_content_parts
        
        result = generate_oracle(final_prompt_content)
        return result

    except Exception as e:
        # This will catch errors from BigQuery client instantiation, query execution, or other processing.
        return {"error": f"An error occurred while processing founder data: {str(e)}"}


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





