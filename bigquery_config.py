"""BigQuery configuration and settings"""

# Google Cloud Platform configuration
GCP_CONFIG = {
    'project_id': 'hackmind-471716',
    'dataset_id': 'hackmind',
    'table_name': 'deal_data'
}

# Analysis configuration
ANALYSIS_CONFIG = {
    'run_competitor_analysis': True,
    'run_devils_advocate': True,
    'update_bigquery': True,
}

def get_project_id():
    """Get the Google Cloud project ID"""
    return GCP_CONFIG['project_id']

def get_dataset_id():
    """Get the BigQuery dataset ID"""
    return GCP_CONFIG['dataset_id']

def get_table_name():
    """Get the BigQuery table name"""
    return GCP_CONFIG['table_name']

def get_table_id():
    """Get the fully qualified BigQuery table ID"""
    return f"{GCP_CONFIG['project_id']}.{GCP_CONFIG['dataset_id']}.{GCP_CONFIG['table_name']}"