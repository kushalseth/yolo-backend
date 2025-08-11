from pymongo import ASCENDING
from pymongo.database import Database


def get_db(client, db_name: str) -> Database:
    return client[db_name]


def ensure_indexes(db: Database):
    db.datasets.create_index([("created_at", ASCENDING)])
    db.images.create_index([("dataset_id", ASCENDING)])
    db.images.create_index([("labels.class_name", ASCENDING)])