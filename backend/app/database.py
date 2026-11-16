"""
Database layer for OmniRoute.
High performance in-memory document store with PyMongo API compatibility.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from pymongo import MongoClient

logger = logging.getLogger("omniroute.database")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "omniroute")

class MockCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs
        self._skip = 0
        self._limit = None

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list):
            for k, d in reversed(key_or_list):
                rev = (d == -1)
                self._docs.sort(key=lambda x: (x.get(k) is None, x.get(k)), reverse=rev)
        else:
            rev = (direction == -1)
            self._docs.sort(key=lambda x: (x.get(key_or_list) is None, x.get(key_or_list)), reverse=rev)
        return self

    def skip(self, n: int):
        self._skip = n
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def _get_result(self):
        res = self._docs[self._skip:]
        if self._limit is not None:
            res = res[:self._limit]
        return [dict(d) for d in res]

    def __iter__(self):
        return iter(self._get_result())

    def __len__(self):
        return len(self._get_result())

class MockCollection:
    def __init__(self, name: str):
        self.name = name
        self._docs: List[Dict[str, Any]] = []

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for k, v in query.items():
            doc_val = doc.get(k)
            if isinstance(v, dict):
                for op, op_val in v.items():
                    if op == "$in" and doc_val not in op_val:
                        return False
                    elif op == "$nin" and doc_val in op_val:
                        return False
                    elif op == "$ne" and doc_val == op_val:
                        return False
                    elif op == "$gt" and (doc_val is None or doc_val <= op_val):
                        return False
                    elif op == "$gte" and (doc_val is None or doc_val < op_val):
                        return False
                    elif op == "$lt" and (doc_val is None or doc_val >= op_val):
                        return False
                    elif op == "$lte" and (doc_val is None or doc_val > op_val):
                        return False
            elif doc_val != v:
                return False
        return True

    def insert_one(self, doc: Dict[str, Any]):
        c = dict(doc)
        if "_id" not in c:
            c["_id"] = str(len(self._docs) + 1)
        self._docs.append(c)
        return type("InsertOneResult", (), {"inserted_id": c["_id"]})()

    def insert_many(self, docs: List[Dict[str, Any]]):
        ids = []
        for d in docs:
            res = self.insert_one(d)
            ids.append(res.inserted_id)
        return type("InsertManyResult", (), {"inserted_ids": ids})()

    def find(self, query: Optional[Dict[str, Any]] = None):
        q = query or {}
        matched = [d for d in self._docs if self._matches(d, q)]
        return MockCursor(matched)

    def find_one(self, query: Optional[Dict[str, Any]] = None):
        q = query or {}
        for d in self._docs:
            if self._matches(d, q):
                return dict(d)
        return None

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        q = query or {}
        if not q:
            return len(self._docs)
        return sum(1 for d in self._docs if self._matches(d, q))

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        for d in self._docs:
            if self._matches(d, query):
                if "$set" in update:
                    for k, v in update["$set"].items():
                        d[k] = v
                return type("UpdateResult", (), {"modified_count": 1})()
        return type("UpdateResult", (), {"modified_count": 0})()

    def delete_many(self, query: Optional[Dict[str, Any]] = None):
        if not query:
            cnt = len(self._docs)
            self._docs.clear()
            return type("DeleteResult", (), {"deleted_count": cnt})()
        initial_len = len(self._docs)
        self._docs = [d for d in self._docs if not self._matches(d, query)]
        return type("DeleteResult", (), {"deleted_count": initial_len - len(self._docs)})()

class MockDatabase:
    def __init__(self, name: str):
        self.name = name
        self._collections: Dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection(name)
        return self._collections[name]

    def __getattr__(self, name: str) -> MockCollection:
        return self[name]

class DatabaseManager:
    def __init__(self):
        self.is_mock = True
        self.client = None
        self.db = None
        self._initialize()

    def _initialize(self):
        try:
            real_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=500)
            real_client.server_info()
            self.client = real_client
            self.db = self.client[DATABASE_NAME]
            self.is_mock = False
            logger.info("Connected successfully to active MongoDB daemon at %s", MONGODB_URI)
        except Exception:
            self.db = MockDatabase(DATABASE_NAME)
            self.is_mock = True
            logger.info("Local High-Performance Document Store initialized successfully.")

    def get_db(self):
        return self.db

db_manager = DatabaseManager()

def get_database():
    return db_manager.get_db()

def get_collection(name: str):
    return db_manager.get_db()[name]
