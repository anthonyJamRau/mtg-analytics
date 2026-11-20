import os
from google.cloud import storage

def get_gcs_client():
    """Initializes the GCS client using Application Default Credentials (ADC)."""
    # The client implicitly searches for local credentials set up via `gcloud auth application-default login`
    # Do NOT pass explicit keys, files, or project IDs here for local dev.
    return storage.Client()

def list_files(client, bucket_name, prefix=None):
    """Lists all files in a bucket, optionally filtered by a folder path (prefix)."""
    bucket = client.bucket(bucket_name)
    
    # Convert to a list immediately so it can be iterated multiple times
    blobs = list(bucket.list_blobs(prefix=prefix))
    
    print(f"\n--- Files in bucket '{bucket_name}' ---")
    for blob in blobs:
        print(f"📄 {blob.name} (Size: {blob.size} bytes)")

    return blobs

def upload_file(client, bucket_name, local_file_path, destination_blob_name):
    """Uploads a local file to the specified GCS bucket."""
    bucket = client.bucket(bucket_name)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    blob.upload_from_filename(local_file_path)
    print(f"✅ Successfully uploaded {local_file_path} to {destination_blob_name}.")

def download_file(client, bucket_name, source_blob_name, local_destination_path):
    """Downloads a file from GCS to your local machine."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    
    blob.download_to_filename(local_destination_path)
    print(f"📥 Successfully downloaded {source_blob_name} to {local_destination_path}.")

def delete_file(client, bucket_name, blob_name):
    """Deletes a file from the bucket."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.delete()
    print(f"❌ Successfully deleted {blob_name} from the bucket.")


if __name__ == "__main__":
    # Replace with your actual bucket name
    MY_BUCKET = "your-gcs-bucket-name"
    
    try:
        # 1. Quick test to see if your ADC has access
        client = get_gcs_client()
        list_files(client, MY_BUCKET)
        
        # 2. Example Upload Workflow (uncomment to test)
        # upload_file(client, MY_BUCKET, "local_test.txt", "uploads/remote_test.txt")
        
        # 3. Example Download Workflow (uncomment to test)
        # download_file(client, MY_BUCKET, "uploads/remote_test.txt", "downloaded_test.txt")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Tip: If you get a 'Permission Denied' or '403' error, verify that your Google account")
        print(f"has the 'Storage Object Viewer' or 'Storage Admin' role assigned to it in the GCP console.")
