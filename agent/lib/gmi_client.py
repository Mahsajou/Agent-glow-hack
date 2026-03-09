"""
GMI Cloud client: LLM (chat completions) + Image (requestqueue).
"""

import base64
import json
import os
import sys
import time
from typing import Optional

import requests

GMI_BASE_URL = "https://api.gmi-serving.com/v1"
GMI_LLM_MODEL = "google/gemini-3.1-pro-preview"
GMI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
GMI_IMAGE_URL = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey/requests"


def _image_url_from_outcome(outcome: dict) -> Optional[str]:
    media = outcome.get("media_urls") or []
    if media:
        first = media[0]
        if isinstance(first, dict) and first.get("url"):
            return first["url"]
        if isinstance(first, str):
            return first
    for k in ("image_url", "url", "output_url"):
        if outcome.get(k):
            return outcome[k]
    for k, v in (outcome or {}).items():
        if isinstance(v, str) and v.startswith("http"):
            return v
    return None


class GmiClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ["GMI_API_KEY"]

    def generate_content(self, prompt: str, model: str = GMI_LLM_MODEL) -> str:
        resp = requests.post(
            f"{GMI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8192,
                "temperature": 0.7,
            },
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        size: str | None = None,
        model: str = GMI_IMAGE_MODEL,
    ) -> tuple[Optional[str], Optional[str]]:
        """Returns (data_uri, error). Success: (uri, None). Failure: (None, msg)."""
        api_key = os.environ.get("GMI_API_KEY") or self._api_key
        if not api_key:
            return None, "GMI_API_KEY not set"

        ratio = aspect_ratio if aspect_ratio in ("4:5", "16:9", "1:1", "4:3") else "16:9"
        payload = {"prompt": prompt, "image_size": size or "1K", "aspect_ratio": ratio}
        body = {"model": model, "payload": payload}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            resp = requests.post(GMI_IMAGE_URL, headers=headers, json=body, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            err = str(e)
            if hasattr(e, "response") and e.response:
                try:
                    b = e.response.json()
                    err = b.get("error", b.get("message", err))
                    if isinstance(err, dict):
                        err = err.get("message", str(err))
                except Exception:
                    pass
            return None, f"Create failed: {err}"

        rid = data.get("request_id") or data.get("id")
        if not rid:
            return None, f"No request_id: {list(data.keys())}"

        outcome = data.get("outcome") or data.get("output") or {}
        if outcome and (url := _image_url_from_outcome(outcome)):
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                b64 = base64.b64encode(r.content).decode("ascii")
                return f"data:image/png;base64,{b64}", None
            except requests.RequestException as e:
                return None, f"Fetch failed: {e}"

        base = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey"
        deadline = time.time() + 90
        while time.time() < deadline:
            try:
                r = requests.get(f"{base}/requests/{rid}", headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
                r.raise_for_status()
                sd = r.json()
            except requests.RequestException:
                time.sleep(2)
                continue
            st = sd.get("status", "")
            if st in ("failed", "error", "canceled", "cancelled"):
                return None, str(sd.get("error", sd.get("message", "Failed")))
            if st in ("success", "completed", "finished"):
                outcome = sd.get("outcome") or sd.get("output") or {}
                if url := _image_url_from_outcome(outcome):
                    try:
                        ir = requests.get(url, timeout=30)
                        ir.raise_for_status()
                        b64 = base64.b64encode(ir.content).decode("ascii")
                        return f"data:image/png;base64,{b64}", None
                    except requests.RequestException as e:
                        return None, str(e)
                return None, "No image URL in outcome"
            time.sleep(2)
        return None, "Timed out"
