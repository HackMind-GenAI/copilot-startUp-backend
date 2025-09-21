#!/usr/bin/env python3
"""
Simple configuration test to validate BigQuery setup
"""

import sys
import os

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.cloud import bigquery
# from bigquery_config import (
#     get_table_id,
#     get_project_id,
#     get_dataset_id, 
#     get_table_name,
#     GCP_CONFIG,
#     TEST_CONFIG,
#     ANALYSIS_CONFIG
# )

def test_configuration():
    """Test the BigQuery configuration and connection"""
    print("🧪 Testing BigQuery Configuration")
    print("=" * 50)
    
    # Display configuration
    print(f"📋 Project ID: {get_project_id()}")
    print(f"📊 Dataset ID: {get_dataset_id()}")
    print(f"🗃️ Table Name: {get_table_name()}")
    print(f"🔗 Full Table ID: {get_table_id()}")
    print(f"🌍 Location: {GCP_CONFIG.get('location', 'US')}")
    
    print("\n⚙️ Analysis Configuration:")
    print(f"  • Competitor Analysis: {'✅ Enabled' if ANALYSIS_CONFIG['run_competitor_analysis'] else '❌ Disabled'}")
    print(f"  • Devil's Advocate: {'✅ Enabled' if ANALYSIS_CONFIG['run_devils_advocate'] else '❌ Disabled'}")
    print(f"  • BigQuery Updates: {'✅ Enabled' if ANALYSIS_CONFIG['update_bigquery'] else '❌ Disabled'}")
    print(f"  • Verbose Logging: {'✅ Enabled' if ANALYSIS_CONFIG['verbose_logging'] else '❌ Disabled'}")
    
    # Test BigQuery connection
    try:
        print("\n🔌 Testing BigQuery Connection...")
        client = bigquery.Client(project=get_project_id())
        
        # Test basic connection by listing datasets
        datasets = list(client.list_datasets())
        print(f"✅ Connected to BigQuery successfully!")
        print(f"📚 Found {len(datasets)} datasets in project")
        
        # Check if our dataset exists
        dataset_exists = False
        for dataset in datasets:
            if dataset.dataset_id == get_dataset_id():
                dataset_exists = True
                print(f"✅ Dataset '{get_dataset_id()}' found!")
                break
        
        if not dataset_exists:
            print(f"⚠️ Dataset '{get_dataset_id()}' not found. You may need to create it.")
        
        # Test table access
        print(f"\n🗃️ Testing table access...")
        table_ref = client.dataset(get_dataset_id()).table(get_table_name())
        
        try:
            table = client.get_table(table_ref)
            print(f"✅ Table '{get_table_name()}' found!")
            print(f"📊 Table has {table.num_rows} rows")
            print(f"🏗️ Table schema has {len(table.schema)} columns")
            
            # Show some column names
            column_names = [field.name for field in table.schema[:10]]  # First 10 columns
            print(f"📋 Sample columns: {', '.join(column_names)}")
            
        except Exception as table_error:
            print(f"❌ Error accessing table: {str(table_error)}")
            print(f"💡 Make sure table '{get_table_name()}' exists in dataset '{get_dataset_id()}'")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {str(e)}")
        print("💡 Make sure:")
        print("   • Google Cloud credentials are configured")
        print("   • Project ID is correct")
        print("   • You have BigQuery access permissions")
        return False
    
    print(f"\n🎉 Configuration test completed successfully!")
    print(f"🚀 Ready to run analysis with sample ID: {TEST_CONFIG['sample_record_id']}")
    return True

def test_sample_record():
    """Test if the sample record exists"""
    try:
        print(f"\n🔍 Testing sample record access...")
        client = bigquery.Client(project=get_project_id())
        
        query = f"""
        SELECT id, created_at
        FROM `{get_table_id()}`
        WHERE id = '{TEST_CONFIG['sample_record_id']}'
        LIMIT 1
        """
        
        query_job = client.query(query)
        results = list(query_job.result())
        
        if results:
            record = dict(results[0])
            print(f"✅ Sample record '{TEST_CONFIG['sample_record_id']}' found!")
            print(f"📅 Created: {record.get('created_at')}")
            return True
        else:
            print(f"⚠️ Sample record '{TEST_CONFIG['sample_record_id']}' not found")
            print("💡 Try using an existing record ID from your table")
            return False
            
    except Exception as e:
        print(f"❌ Error testing sample record: {str(e)}")
        return False

if __name__ == "__main__":
    print("BigQuery Analysis Test Configuration")
    print("=" * 60)
    
    # Test configuration and connection
    config_success = test_configuration()
    
    if config_success:
        # Test sample record
        record_success = test_sample_record()
        
        if record_success:
            print(f"\n✅ All tests passed! Ready to run full analysis.")
            print(f"▶️ Run: python test_bigquery_analysis.py {TEST_CONFIG['sample_record_id']}")
        else:
            print(f"\n⚠️ Configuration OK, but sample record not found.")
            print("💡 Update the sample_record_id in bigquery_config.py or use a different ID")
    else:
        print(f"\n❌ Configuration test failed. Please fix the issues above.")
    
    print("\n" + "=" * 60)
