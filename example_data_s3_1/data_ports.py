from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast

from muscles_data import DataCapability
from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.ports import ObjectStorePort
from muscles_data.runtime import DataRuntime
from muscles_data_s3 import S3ObjectStoreFactory

from example_data_common import development_approach
from example_data_common.fakes import FakeS3Client


def run_example() -> dict:
    client = FakeS3Client()
    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(S3ObjectStoreFactory(client_factory=lambda _config: client))
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {"data": {"resources": {"objects.docs": {"type": "s3", "endpoint_url": "https://user:s3-secret@s3.example", "bucket": "documents", "region_name": "us-east-1", "prefix": "raw", "max_keys": 5, "native_client": True}}}}
        ),
        catalog=catalog,
    )

    initialized_before = runtime.list_resources()[0]["initialized"]
    objects = cast(ObjectStorePort, runtime.require_port("objects.docs", ObjectStorePort))
    put = objects.put_object("docs/readme.txt", b"hello", content_type="text/plain", metadata={"owner": "denis"})
    blob = objects.get_object("docs/readme.txt")
    objects.put_object("docs/guide.txt", b"guide")
    listed = objects.list_objects(prefix="docs", limit=10)
    deleted = objects.delete_object("docs/guide.txt")
    native = runtime.require_resource("objects.docs", DataCapability.NATIVE_CLIENT).native_client()

    return {
        "approach": development_approach(),
        "initialized_before": initialized_before,
        "put": asdict(put),
        "blob": {"key": blob.key, "content": blob.content.decode("utf-8"), "content_type": blob.content_type},
        "listed_keys": [item.key for item in listed],
        "stored_keys": [key for _bucket, key in sorted(client.objects)],
        "deleted": asdict(deleted),
        "native_type": native.__class__.__name__,
        "inspect": runtime.inspect_resource("objects.docs"),
        "doctor": runtime.doctor(),
    }


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
