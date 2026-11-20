# From clicks in GCP UI

## Command Line
```cmd
gcloud storage buckets create gs://seventeen-lands-open-data \
    --default-storage-class=NEARLINE \
    --location=US-CENTRAL1 \
    --uniform-bucket-level-access \
    --public-access-prevention
```

## REST
```python
POST https://storage.googleapis.com/storage/v1/b?project=mtg-analytics-514317
{
  "encryption": {},
  "iamConfiguration": {
    "uniformBucketLevelAccess": {
      "enabled": true
    },
    "publicAccessPrevention": "enforced"
  },
  "location": "US-CENTRAL1",
  "name": "seventeen-lands-open-data",
  "storageClass": "NEARLINE"
}
```
