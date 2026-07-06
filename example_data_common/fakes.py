from __future__ import annotations

from types import SimpleNamespace
from typing import Any


class FakeElasticsearchIndices:
    def exists(self, *, index: str) -> bool:
        return index == "docs"


class FakeElasticsearchClient:
    def __init__(self) -> None:
        self.indices = FakeElasticsearchIndices()

    def search(self, **_kwargs):
        return {
            "hits": {
                "hits": [
                    {
                        "_id": "doc-1",
                        "_score": 3.2,
                        "_source": {"text": "Muscles data ports", "metadata": {"section": "docs"}},
                        "highlight": {"text": ["<em>Muscles</em> data ports"]},
                    }
                ]
            }
        }

    def index(self, **_kwargs):
        return {"result": "created"}

    def delete(self, **_kwargs):
        return {"result": "deleted"}

    def delete_by_query(self, **_kwargs):
        return {"deleted": 1}

    def ping(self) -> bool:
        return True


class FakeOpenSearchIndices:
    def exists(self, *, index: str) -> bool:
        return index == "docs"


class FakeOpenSearchClient:
    def __init__(self) -> None:
        self.indices = FakeOpenSearchIndices()

    def search(self, **_kwargs):
        return {
            "hits": {
                "hits": [
                    {
                        "_id": "doc-1",
                        "_score": 3.2,
                        "_source": {"text": "Muscles data ports", "metadata": {"section": "docs"}},
                        "highlight": {"text": ["<em>Muscles</em> data ports"]},
                    }
                ]
            }
        }

    def index(self, **_kwargs):
        return {"result": "created"}

    def delete(self, **_kwargs):
        return {"result": "deleted"}

    def delete_by_query(self, **_kwargs):
        return {"deleted": 1}

    def ping(self) -> bool:
        return True


class FakeRedisClient:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}
        self.streams: dict[str, list[tuple[str, dict[str, Any]]]] = {}

    def set(self, name: str, value, **kwargs):
        if kwargs.get("nx") and name in self.values:
            return False
        self.values[name] = value
        return True

    def get(self, name: str):
        return self.values.get(name)

    def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            deleted += 1 if self.values.pop(name, None) is not None else 0
        return deleted

    def exists(self, *names: str) -> int:
        return sum(1 for name in names if name in self.values)

    def eval(self, _script: str, _numkeys: int, key: str, expected_token: str):
        if self.values.get(key) != expected_token:
            return 0
        self.values.pop(key, None)
        return 1

    def xadd(self, name: str, fields: dict[str, Any]):
        stream = self.streams.setdefault(name, [])
        message_id = f"{len(stream) + 1}-0"
        stream.append((message_id, dict(fields)))
        return message_id

    def xread(self, streams: dict[str, str], count: int | None = None, block: int | None = None):
        del block
        output = []
        for name, cursor in streams.items():
            messages = [
                (message_id, fields)
                for message_id, fields in self.streams.get(name, [])
                if cursor in {"0", "0-0"} or message_id > cursor
            ]
            output.append((name, messages[:count]))
        return output

    def xack(self, name: str, _groupname: str, *ids: str) -> int:
        known = {message_id for message_id, _fields in self.streams.get(name, [])}
        return sum(1 for message_id in ids if message_id in known)

    def ping(self) -> bool:
        return True


class FakeS3Body:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def read(self) -> bytes:
        return self.content


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, Any]] = {}

    def put_object(self, **kwargs):
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = {
            "Body": bytes(kwargs["Body"]),
            "ContentType": kwargs.get("ContentType"),
            "Metadata": dict(kwargs.get("Metadata") or {}),
        }
        return {"ETag": '"example"'}

    def get_object(self, **kwargs):
        item = self.objects[(kwargs["Bucket"], kwargs["Key"])]
        return {
            "Body": FakeS3Body(item["Body"]),
            "ContentType": item.get("ContentType"),
            "Metadata": dict(item.get("Metadata") or {}),
        }

    def list_objects_v2(self, **kwargs):
        bucket = kwargs["Bucket"]
        prefix = kwargs.get("Prefix", "")
        max_keys = int(kwargs.get("MaxKeys", 100))
        contents = [
            {"Key": key, "Size": len(item["Body"])}
            for (stored_bucket, key), item in sorted(self.objects.items())
            if stored_bucket == bucket and key.startswith(prefix)
        ]
        return {"Contents": contents[:max_keys]}

    def delete_object(self, **kwargs):
        self.objects.pop((kwargs["Bucket"], kwargs["Key"]), None)
        return {}

    def head_bucket(self, **_kwargs):
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


class FakeMongoAdmin:
    def command(self, _name: str):
        return {"ok": 1}


class FakeMongoCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs
        self.limit_value: int | None = None

    def limit(self, value: int):
        self.limit_value = value
        return self

    def __iter__(self):
        return iter(self.docs[: self.limit_value])


class FakeMongoCollection:
    def __init__(self) -> None:
        self.docs: dict[str, dict[str, Any]] = {}

    def find_one(self, filter):
        doc = self.docs.get(str(filter.get("_id")))
        return dict(doc) if doc is not None else None

    def replace_one(self, filter, replacement, upsert: bool = False):
        del upsert
        document_id = str(filter["_id"])
        matched = 1 if document_id in self.docs else 0
        self.docs[document_id] = dict(replacement)
        return SimpleNamespace(matched_count=matched, modified_count=1 if matched else 0)

    def find(self, filter):
        docs = [
            dict(doc)
            for doc in self.docs.values()
            if all(doc.get(key) == value for key, value in dict(filter).items())
        ]
        return FakeMongoCursor(docs)

    def delete_one(self, filter):
        deleted = 1 if self.docs.pop(str(filter.get("_id")), None) is not None else 0
        return SimpleNamespace(deleted_count=deleted)


class FakeMongoDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeMongoCollection] = {}

    def __getitem__(self, name: str) -> FakeMongoCollection:
        return self.collections.setdefault(name, FakeMongoCollection())


class FakeMongoClient:
    def __init__(self) -> None:
        self.admin = FakeMongoAdmin()
        self.databases: dict[str, FakeMongoDatabase] = {}

    def __getitem__(self, name: str) -> FakeMongoDatabase:
        return self.databases.setdefault(name, FakeMongoDatabase())

    def close(self) -> None:
        return None


class FakeQdrantPoint:
    def __init__(self, point_id: str, score: float, payload: dict[str, Any]) -> None:
        self.id = point_id
        self.score = score
        self.payload = payload


class FakeQdrantQueryResult:
    def __init__(self, points: list[FakeQdrantPoint]) -> None:
        self.points = points


class FakeQdrantClient:
    def __init__(self) -> None:
        self.collection = "docs"

    def query_points(self, **_kwargs):
        return FakeQdrantQueryResult([
            FakeQdrantPoint("doc-1", 0.92, {"section": "docs"}),
        ])

    def upsert(self, **_kwargs):
        return {"status": "completed"}

    def delete(self, **_kwargs):
        return {"status": "completed"}

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name == self.collection


class FakeQdrantModels:
    class MatchValue:
        def __init__(self, value) -> None:
            self.value = value

    class MatchAny:
        def __init__(self, any) -> None:
            self.any = any

    class Range:
        def __init__(self, **kwargs) -> None:
            self.values = kwargs

    class FieldCondition:
        def __init__(self, *, key: str, match=None, range=None) -> None:
            self.key = key
            self.match = match
            self.range = range

    class Filter:
        def __init__(self, *, must=None, should=None, must_not=None) -> None:
            self.must = must or []
            self.should = should or []
            self.must_not = must_not or []

    class PointStruct:
        def __init__(self, *, id, vector, payload=None) -> None:
            self.id = id
            self.vector = vector
            self.payload = payload or {}

    class PointIdsList:
        def __init__(self, *, points) -> None:
            self.points = points

    class FilterSelector:
        def __init__(self, *, filter) -> None:
            self.filter = filter
