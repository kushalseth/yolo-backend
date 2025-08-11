import os
import uuid
import shutil
import datetime
from zipfile import ZipFile
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from pymongo import MongoClient, ASCENDING

from .yolo import parse_yolo_dir
from .storage import upload_dir_to_gcs, signed_url_for
from .models import get_db, ensure_indexes

app = FastAPI(title="YOLO Dataset Backend")

BUCKET = os.getenv("GCS_BUCKET", "your-dataset-bucket")
DB_NAME = os.getenv("DB_NAME", "annotation")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)
db = get_db(client, DB_NAME)
ensure_indexes(db)

@app.post("/import-dataset")
async def import_dataset(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip supported")

    dataset_id = str(uuid.uuid4())
    dataset_name = os.path.splitext(os.path.basename(file.filename))[0]
    created_at = datetime.datetime.utcnow()

    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    extract_dir = f"/tmp/{dataset_id}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        parsed = parse_yolo_dir(extract_dir)
        classes = parsed["classes"]
        images = parsed["images"]

        gcs_prefix = f"datasets/{dataset_id}/"
        upload_dir_to_gcs(local_root=extract_dir, bucket_name=BUCKET, prefix=gcs_prefix)

        db.datasets.insert_one({
            "_id": dataset_id,
            "name": dataset_name,
            "created_at": created_at,
            "image_count": len(images),
            "classes": classes,
            "gcs_prefix": gcs_prefix,
        })

        if images:
            docs = []
            for img in images:
                rel = os.path.relpath(img["local_path"], extract_dir)
                docs.append({
                    "_id": str(uuid.uuid4()),
                    "dataset_id": dataset_id,
                    "path": f"gs://{BUCKET}/{gcs_prefix}{rel}",
                    "w": img.get("w"),
                    "h": img.get("h"),
                    "labels": img.get("labels", []),
                })
            db.images.insert_many(docs)

        return {"message": "Dataset imported successfully", "id": dataset_id}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass

@app.get("/datasets")
async def list_datasets(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200)):
    skip = (page - 1) * page_size
    cursor = db.datasets.find({}, {"classes": 0}).sort("created_at", ASCENDING).skip(skip).limit(page_size)
    items = [{
        "id": d["_id"],
        "name": d.get("name"),
        "created_at": d.get("created_at"),
        "image_count": d.get("image_count"),
    } for d in cursor]
    return {"page": page, "page_size": page_size, "items": items}

@app.get("/datasets/{dataset_id}/images")
async def list_images(dataset_id: str,
                      page: int = Query(1, ge=1),
                      page_size: int = Query(50, ge=1, le=500),
                      class_name: Optional[str] = Query(None, alias="class"),
                      signed_url: bool = Query(False)):
    q = {"dataset_id": dataset_id}
    if class_name:
        q["labels.class_name"] = class_name
    skip = (page - 1) * page_size
    cursor = db.images.find(q).skip(skip).limit(page_size)
    items = []
    for img in cursor:
        rec = {
            "id": img["_id"],
            "path": img["path"],
            "w": img.get("w"),
            "h": img.get("h"),
            "labels": img.get("labels", []),
        }
        if signed_url:
            rec["signed_url"] = signed_url_for(img["path"], expires_minutes=60)
        items.append(rec)
    return {"page": page, "page_size": page_size, "items": items}