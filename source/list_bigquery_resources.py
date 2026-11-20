import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

def list_bigquery_resources(project_id=None):
    """
    Lists all datasets in a project, and lists all tables within each dataset
    using Application Default Credentials (ADC).
    """
    # If project_id is not passed, the client automatically infers it 
    # from your ADC or active gcloud configuration.
    try:
        client = bigquery.Client(project=project_id)
        target_project = client.project
        print(f"Using Google Cloud Project: {target_project}\n")
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client. "
              f"Did you run 'gcloud auth application-default login'?\nError: {e}")
        return

    # 1. List all Datasets in the Project
    try:
        datasets = list(client.list_datasets())
    except Exception as e:
        print(f"❌ Failed to list datasets for project '{target_project}': {e}")
        return

    if not datasets:
        print(f"ℹ️ No datasets found in project '{target_project}'.")
        return

    print(f"📂 Found {len(datasets)} dataset(s) in project '{target_project}':")
    for dataset in datasets:
        dataset_id = dataset.dataset_id
        print(f"\n--- Dataset: {dataset_id} ---")
        
        # Reference the specific dataset to list its tables
        dataset_ref = client.dataset(dataset_id)
        
        # 2. List all Tables in the Dataset
        try:
            tables = list(client.list_tables(dataset_ref))
            if not tables:
                print("  (No tables found in this dataset)")
                continue
                
            for table in tables:
                # table.table_type can be 'TABLE', 'VIEW', or 'EXTERNAL'
                print(f"  🔹 [{table.table_type}] {table.table_id}")
        except Exception as e:
            print(f"  ❌ Error listing tables in dataset '{dataset_id}': {e}")

if __name__ == "__main__":
    # REPLACE with your GCP Project ID, or leave as None to auto-detect
    GCP_PROJECT_ID = None 
    
    list_bigquery_resources(project_id=GCP_PROJECT_ID)
