"""Pre-flight checks for worker dependencies. Run before worker starts."""

import os
import sys
from pathlib import Path


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _check_qdrant(url: str, timeout: float = 5.0) -> str | None:
    """Return error message or None if Qdrant is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{url.rstrip('/')}/healthz", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status in (200, 204):
                return None
            return f"Qdrant health returned {resp.status}"
    except Exception as e:
        return str(e)


def _check_storage() -> str | None:
    """Return error message or None if storage is OK."""
    backend = _get_env("STORAGE_BACKEND", "fs").lower()
    if backend == "fs":
        output_dir = _get_env("AGENT_OUTPUT_DIR") or str(Path(__file__).parent.parent / "output")
        p = Path(output_dir)
        try:
            p.mkdir(parents=True, exist_ok=True)
            (p / ".precheck").write_text("ok")
            (p / ".precheck").unlink()
            return None
        except Exception as e:
            return f"Storage (fs) {output_dir}: {e}"
    if backend == "s3":
        bucket = _get_env("S3_BUCKET")
        if not bucket:
            return "S3_BUCKET required when STORAGE_BACKEND=s3"
        try:
            import boto3
            from botocore.config import Config
            kw: dict = {"region_name": _get_env("S3_REGION") or "us-east-1"}
            if _get_env("S3_ENDPOINT_URL"):
                kw["endpoint_url"] = _get_env("S3_ENDPOINT_URL")
                kw["config"] = Config(signature_version="s3v4")
            client = boto3.client("s3", **kw)
            client.head_bucket(Bucket=bucket)
            return None
        except Exception as e:
            return f"Storage (S3) bucket={bucket}: {e}"
    return f"Unknown STORAGE_BACKEND: {backend}"


def run_prechecks() -> list[str]:
    """
    Run all pre-flight checks. Returns list of error messages (empty if all OK).
    On error, caller should log and exit.
    """
    errors: list[str] = []

    # Storage
    err = _check_storage()
    if err:
        errors.append(err)

    # Qdrant — use same default as agent.lib.rag
    qdrant_url = _get_env("QDRANT_URL", "http://localhost:6333")
    err = _check_qdrant(qdrant_url)
    if err:
        errors.append(f"Qdrant ({qdrant_url}): {err}")

    return errors
