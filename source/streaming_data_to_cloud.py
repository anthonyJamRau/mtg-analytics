import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from urllib.parse import urlparse
import tempfile
import source.helpers.gcs_helper as gcs
import source.helpers.seventeen_lands_dtypes as dtypes

def stream_url_to_gcs_parquet(
    public_url: str,
    gcs_client: gcs.Client,
    gcs_bucket: str,
    gcs_blob_name: str,
    chunksize: int = 100000,
    size_threshold_mb: float = 100.0
):
    print(f"Processing URL: {public_url}")

    # 1. Gracefully check if the URL exists and inspect file size via HTTP HEAD
    try:
        response = requests.head(public_url, allow_redirects=True, verify=False)
        
        if response.status_code >= 400:
            print(f"Skipping URL due to HTTP status {response.status_code}: {public_url}")
            return
            
        content_length = int(response.headers.get('Content-Length', 0))
        file_size_mb = content_length / (1024 * 1024)
        print(f"Detected file size: {file_size_mb:.2f} MB")
        
    except requests.exceptions.RequestException as e:
        print(f"Connection or HTTP error for {public_url}: {e}. Skipping...")
        return
    except Exception as e:
        print(f"Could not determine file size ({e}), defaulting to chunked stream...")
        file_size_mb = size_threshold_mb + 1

    # 2. Automatically detect format and compression from the URL path
    parsed_url = urlparse(public_url)
    path = parsed_url.path.lower()

    compression = 'gzip' if path.endswith('.gz') else None

    if 'jsonl' in path or path.endswith('.json'):
        file_format = 'jsonl'
    else:
        file_format = 'csv'

    print(f"Detected Format: {file_format.upper()} | Compression: {compression or 'None'}")

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
        temp_path = tmp_file.name

    try:
        # Get dynamic dtypes and sanitize their keys to match cleaned field names
        raw_dtypes = dtypes.get_dtypes(public_url, print_missing=False)
        all_dtypes = {dtypes.sanitize_column_name(k): v for k, v in raw_dtypes.items()}
        
        # Pandas C-parser does not support float16 natively in dtype dict. 
        # Separate float16 columns to apply them safely post-load.
        csv_read_dtypes = {k: v for k, v in all_dtypes.items() if v != 'float16'}
        print(f"Mapped {len(all_dtypes)} types ({len(csv_read_dtypes)} passed directly to reader).")

        if file_size_mb < size_threshold_mb:
            print("File is small. Loading all at once...")
            
            if file_format == 'jsonl':
                df = pd.read_json(public_url, lines=True, compression=compression)
            else:
                df = pd.read_csv(public_url, compression=compression, dtype=csv_read_dtypes, low_memory=False)
                
            # Sanitize column names right after loading
            df.columns = [dtypes.sanitize_column_name(c) for c in df.columns]

            # Safely apply all dtypes (including float16) post-load
            for col, dtype in all_dtypes.items():
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(dtype)
                    except Exception:
                        pass

            df.to_parquet(temp_path, engine='pyarrow', compression='snappy')
            
        else:
            print(f"File is large. Reading and chunking data directly from URL (chunksize={chunksize})...")
            writer = None
            
            if file_format == 'jsonl':
                data_iterator = pd.read_json(public_url, lines=True, compression=compression, chunksize=chunksize)
            else:
                data_iterator = pd.read_csv(public_url, compression=compression, dtype=csv_read_dtypes, chunksize=chunksize, low_memory=False)

            for chunk in data_iterator:
                # Sanitize column names for each chunk
                chunk.columns = [dtypes.sanitize_column_name(c) for c in chunk.columns]

                # Enforce all column types chunk-by-chunk (including float16)
                for col, dtype in all_dtypes.items():
                    if col in chunk.columns:
                        try:
                            chunk[col] = chunk[col].astype(dtype)
                        except Exception:
                            pass

                table = pa.Table.from_pandas(chunk)
                
                if writer is None:
                    writer = pq.ParquetWriter(temp_path, table.schema, compression='snappy')
                
                writer.write_table(table)
                
            if writer:
                writer.close()

    except requests.exceptions.RequestException as e:
        print(f"Request failed during download/stream for {public_url}: {e}. Skipping...")
        return
    except Exception as e:
        print(f"Error during processing of {public_url}: {e}")
        raise

    print(f"Uploading Snappy Parquet to gs://{gcs_bucket}/{gcs_blob_name}...")
    gcs.upload_file(gcs_client, gcs_bucket, temp_path, gcs_blob_name)
    print("Upload complete!")