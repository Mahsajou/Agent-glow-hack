"""
Workflow state storage abstraction.

Supports local filesystem and S3. Use STORAGE_BACKEND=fs|s3 to switch.
"""

from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class WorkflowStore(Protocol):
    """Protocol for workflow state storage. Activities use this to read/write artifacts."""

    def read_json(self, key: str) -> dict | None:
        """Read JSON. Returns None if not found."""
        ...

    def write_json(self, key: str, data: dict) -> None:
        """Write JSON."""
        ...

    def read_blob(self, key: str) -> bytes | None:
        """Read raw bytes. Returns None if not found."""
        ...

    def write_blob(self, key: str, data: bytes) -> None:
        """Write raw bytes."""
        ...

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...

    def directory(self) -> Path:
        """Return a Path to the working directory for this prefix.
        For FS: real directory. For S3: use work_directory() context manager instead.
        """
        ...


class LocalFileStore:
    """Store backed by local filesystem."""

    def __init__(self, base_path: str | Path, prefix: str = ""):
        self._root = Path(base_path)
        if prefix:
            self._root = self._root / prefix
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._root / key

    def read_json(self, key: str) -> dict | None:
        p = self._path(key)
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def write_json(self, key: str, data: dict) -> None:
        self._path(key).write_text(json.dumps(data, indent=2))

    def read_blob(self, key: str) -> bytes | None:
        p = self._path(key)
        if not p.exists():
            return None
        return p.read_bytes()

    def write_blob(self, key: str, data: bytes) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def directory(self) -> Path:
        return self._root


class S3Store:
    """Store backed by S3 or S3-compatible storage (e.g. MinIO). Uses boto3."""

    def __init__(self, bucket: str, prefix: str, region: str | None = None, endpoint_url: str | None = None):
        import boto3
        from botocore.config import Config
        self._bucket = bucket
        self._prefix = prefix.rstrip("/")
        kw: dict = {"region_name": region or "us-east-1"}
        if endpoint_url:
            kw["endpoint_url"] = endpoint_url
            kw["config"] = Config(signature_version="s3v4")  # MinIO requires v4
        self._client = boto3.client("s3", **kw)

    def _key(self, name: str) -> str:
        if self._prefix:
            return f"{self._prefix}/{name}"
        return name

    def read_json(self, key: str) -> dict | None:
        b = self.read_blob(key)
        if b is None:
            return None
        return json.loads(b.decode("utf-8"))

    def write_json(self, key: str, data: dict) -> None:
        self.write_blob(key, json.dumps(data, indent=2).encode("utf-8"))

    def _is_key_not_found(self, e: BaseException) -> bool:
        """True if the exception indicates the key does not exist."""
        if "NoSuchKey" in type(e).__name__:
            return True
        try:
            resp = getattr(e, "response", None)
            if resp is not None:
                code = (resp.get("Error") or {}).get("Code", "")
                if code in ("404", "NoSuchKey"):
                    return True
        except (AttributeError, TypeError):
            pass
        return False

    def read_blob(self, key: str) -> bytes | None:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=self._key(key))
            return resp["Body"].read()
        except Exception as e:
            if self._is_key_not_found(e):
                return None
            raise

    def write_blob(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=self._key(key), Body=data)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=self._key(key))
            return True
        except Exception as e:
            if self._is_key_not_found(e):
                return False
            raise

    def directory(self) -> Path:
        raise NotImplementedError("S3Store has no local directory. Use work_directory() context manager.")

    @contextmanager
    def work_directory(self) -> Path:
        """Sync S3 prefix to temp dir, yield Path, upload changes back. Use for agents that need Path."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Download existing objects
            paginator = self._client.get_paginator("list_objects_v2")
            pfx = self._prefix + "/" if self._prefix else ""
            for page in paginator.paginate(Bucket=self._bucket, Prefix=pfx):
                for obj in page.get("Contents") or []:
                    k = obj["Key"]
                    if k.endswith("/"):
                        continue
                    rel = k[len(pfx):] if pfx and k.startswith(pfx) else k
                    target = tmp_path / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = self._client.get_object(Bucket=self._bucket, Key=k)["Body"].read()
                    target.write_bytes(data)
            yield tmp_path
            # Upload new/changed files
            for f in tmp_path.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(tmp_path)
                    key = self._key(str(rel))
                    self.write_blob(str(rel), f.read_bytes())


def create_store(
    backend: str,
    base_or_prefix: str,
    *,
    s3_bucket: str | None = None,
    s3_region: str | None = None,
    s3_endpoint_url: str | None = None,
) -> WorkflowStore:
    """Create a WorkflowStore from config.
    - backend: 'fs' or 's3'
    - base_or_prefix: for fs, the base directory path; for s3, the key prefix
    - s3_bucket: required when backend='s3'
    - s3_endpoint_url: for MinIO or custom S3-compatible endpoints (e.g. http://localhost:9000)
    """
    if backend == "fs":
        return LocalFileStore(base_or_prefix, prefix="")
    if backend == "s3":
        if not s3_bucket:
            raise ValueError("S3_BUCKET required when STORAGE_BACKEND=s3")
        return S3Store(
            bucket=s3_bucket,
            prefix=base_or_prefix,
            region=s3_region,
            endpoint_url=s3_endpoint_url,
        )
    raise ValueError(f"Unknown STORAGE_BACKEND: {backend}")
