from __future__ import annotations

from dataclasses import asdict
import json
import os
from typing import cast
from uuid import uuid4

from muscles_data.ports import ObjectStorePort
from muscles_data_s3 import S3ObjectStoreFactory

from example_data_common import development_approach
from example_data_common.runtime import build_runtime, local_endpoint


def run_example() -> dict:
    """Run object put/get/list/delete operations against a live S3-compatible service."""

    prefix = f"docs/{uuid4().hex[:12]}"
    first_key = f"{prefix}/readme.txt"
    second_key = f"{prefix}/guide.txt"
    runtime = build_runtime(
        "objects.docs",
        {
            "type": "s3",
            "endpoint_url": local_endpoint("S3_ENDPOINT_URL"),
            "bucket": os.getenv("S3_BUCKET", "muscular-example"),
            "region_name": "us-east-1",
            "aws_access_key_id": os.getenv("S3_ACCESS_KEY", "minioadmin"),
            "aws_secret_access_key": os.getenv("S3_SECRET_KEY", "minioadmin"),
            "prefix": "raw",
            "max_keys": 10,
            "addressing_style": "path",
            "native_client": False,
        },
        S3ObjectStoreFactory(),
    )
    try:
        initialized_before = runtime.list_resources()[0]["initialized"]
        objects = cast(ObjectStorePort, runtime.require_port("objects.docs", ObjectStorePort))
        put = objects.put_object(first_key, b"hello", content_type="text/plain", metadata={"owner": "example"})
        blob = objects.get_object(first_key)
        objects.put_object(second_key, b"guide")
        listed = objects.list_objects(prefix=prefix, limit=10)
        deleted = objects.delete_object(second_key)
        inspection = runtime.inspect_resource("objects.docs")

        return {
            "backend": "s3",
            "approach": development_approach(),
            "initialized_before": initialized_before,
            "put": asdict(put),
            "blob": {"key": blob.key, "content": blob.content.decode("utf-8"), "content_type": blob.content_type},
            "listed_keys": [item.key for item in listed],
            "second_key": second_key,
            "deleted": asdict(deleted),
            "inspect": {
                "status": inspection["status"],
                "details": inspection["details"],
            },
            "doctor": runtime.doctor(),
        }
    finally:
        runtime.close()


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
