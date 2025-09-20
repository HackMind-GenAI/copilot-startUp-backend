import os
import json
from typing import Optional

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account

_bq_client: Optional[bigquery.Client] = None


def get_bq_client(project: Optional[str] = None) -> bigquery.Client:
    """Lazily create and cache a BigQuery client.

    Tries in order:
    1. Default Application Credentials (GOOGLE_APPLICATION_CREDENTIALS or ADC)
    2. `GOOGLE_CREDENTIALS_JSON` environment variable containing service account JSON

    Raises RuntimeError with a helpful message if neither is available.
    """
    global _bq_client
    if _bq_client is not None:
        return _bq_client

    # Try ADC / default credentials first
    try:
        _bq_client = bigquery.Client(project=project)
        return _bq_client
    except DefaultCredentialsError:
        # fall through to try env var
        pass
    except Exception:
        # other errors (network etc) — re-raise as runtime
        try:
            _bq_client = bigquery.Client(project=project)
            return _bq_client
        except Exception as e:
            raise RuntimeError(f"Failed to initialize BigQuery client: {e}") from e

    # Try GOOGLE_CREDENTIALS_JSON (fileless)
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            info = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(info)
            _bq_client = bigquery.Client(credentials=creds, project=project or info.get("project_id"))
            return _bq_client
        except Exception as e:
            raise RuntimeError(f"Failed to create BigQuery client from GOOGLE_CREDENTIALS_JSON: {e}") from e

    raise RuntimeError(
        "BigQuery credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS (path to key file), "
        "or set GOOGLE_CREDENTIALS_JSON containing the service account JSON."
    )
