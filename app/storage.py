import os
import mimetypes
import datetime
import os
from urllib.parse import urlparse
from google.cloud import storage

_gcs_client = None

def gcs_client():
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client()
    return _gcs_client


def upload_dir_to_gcs(local_root: str, bucket_name: str, prefix: str):
    client = gcs_client()
    bucket = client.bucket(bucket_name)
    for dirpath, _, filenames in os.walk(local_root):
        for fn in filenames:
            lp = os.path.join(dirpath, fn)
            rel = os.path.relpath(lp, local_root)
            gp = f"{prefix}{rel}"
            blob = bucket.blob(gp)
            blob.upload_from_filename(lp, content_type=mimetypes.guess_type(lp)[0] or "application/octet-stream")


def signed_url_for(gs_path: str, expires_minutes: int = 60):
    """Generate a V4 signed URL for a gs://bucket/object path."""
    parsed = urlparse(gs_path)
    bucket_name = parsed.netloc
    object_name = parsed.path.lstrip('/')
    client = gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expires_minutes),
        method="GET",
    )