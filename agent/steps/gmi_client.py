"""
GMI Cloud client: LLM (chat/completions) + Image (requestqueue).
- LLM: google/gemini-3.1-pro-preview via api.gmi-serving.com
- Image: gemini-3.1-flash-image-preview via console.gmicloud.ai requestqueue
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
    """Extract image URL from outcome (media_urls, image_url, url, etc)."""
    media = outcome.get("media_urls") or []
    if media:
        first = media[0]
        if isinstance(first, dict):
            u = first.get("url")
            if u:
                return u
        if isinstance(first, str):
            return first
    url = outcome.get("image_url") or outcome.get("url") or outcome.get("output_url")
    if url:
        return url
    imgs = outcome.get("images")
    if isinstance(imgs, list) and imgs:
        return imgs[0] if isinstance(imgs[0], str) else imgs[0].get("url")
    for k, v in (outcome if isinstance(outcome, dict) else {}).items():
        if v and isinstance(v, str) and v.startswith("http"):
            return v
    return None


def _gemini_image_payload(ratio: str, image_size: str) -> dict:
    # gemini-3.1-flash-image-preview: image_size "1K", aspect_ratio "4:5"|"16:9" etc
    return {
        "prompt": "",  # filled by caller
        "image_size": image_size or "1K",
        "aspect_ratio": ratio if ratio in ("4:5", "16:9", "1:1", "4:3") else "16:9",
    }


class _GmiResponse:
    def __init__(self, text: str):
        self.text = text


class _GmiModels:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def generate_content(self, *, model: str, contents: list, config=None) -> _GmiResponse:
        max_tokens = 8192
        if config and hasattr(config, "max_output_tokens"):
            max_tokens = config.max_output_tokens
        prompt_text = contents[0] if isinstance(contents[0], str) else str(contents[0])

        resp = requests.post(
            f"{GMI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt_text}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return _GmiResponse(text)


class _GmiClient:
    def __init__(self, api_key: str):
        self.models = _GmiModels(api_key)


def get_gmi_client(model_id: str = None):
    return _GmiClient(api_key=os.environ["GMI_API_KEY"])


def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    size: str = None,
    model: str = GMI_IMAGE_MODEL,
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate an image via GMI requestqueue (gemini-3.1-flash-image-preview).
    Returns (data_uri, error_message). Success: (uri, None). Failure: (None, "reason").
    """
    api_key = os.environ.get("GMI_API_KEY")
    if not api_key:
        return None, "GMI_API_KEY not set"

    payload = _gemini_image_payload(aspect_ratio, size or "1K")
    payload["prompt"] = prompt

    body = {"model": model, "payload": payload}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    debug = {
        "image_request": {
            "url": GMI_IMAGE_URL,
            "method": "POST",
            "headers": {k: (v[:20] + "..." if k.lower() == "authorization" and len(v) > 20 else v) for k, v in headers.items()},
            "body": body,
        }
    }
    print(json.dumps(debug, indent=2), file=sys.stderr, flush=True)

    try:
        resp = requests.post(GMI_IMAGE_URL, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        err = str(e)
        if hasattr(e, "response") and e.response is not None:
            try:
                body = e.response.json()
                err = body.get("error", body.get("message", err))
                if isinstance(err, dict):
                    err = err.get("message", str(err))
            except Exception:
                pass
        return None, f"Create request failed: {err}"

    request_id = data.get("request_id") or data.get("id")
    if not request_id:
        return None, f"No request_id in response: {list(data.keys())}"

    # Check if image is in initial response (sync)
    outcome = data.get("outcome") or data.get("output") or {}
    if outcome:
        url = _image_url_from_outcome(outcome)
        if url:
            try:
                ir = requests.get(url, timeout=30)
                ir.raise_for_status()
                b64 = base64.b64encode(ir.content).decode("ascii")
                return f"data:image/png;base64,{b64}", None
            except requests.RequestException as e:
                return None, f"Fetch image failed: {e}"

    base_url = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey"
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + 90

    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/requests/{request_id}", headers=headers, timeout=30)
            r.raise_for_status()
            status_data = r.json()
        except requests.RequestException as e:
            time.sleep(2)
            continue

        status = status_data.get("status", "")
        if status in ("failed", "error", "canceled", "cancelled"):
            err = status_data.get("error", status_data.get("message", "Generation failed"))
            return None, str(err)

        if status in ("success", "completed", "finished"):
            outcome = status_data.get("outcome") or status_data.get("output") or {}
            url = _image_url_from_outcome(outcome)
            if url:
                try:
                    ir = requests.get(url, timeout=30)
                    ir.raise_for_status()
                    b64 = base64.b64encode(ir.content).decode("ascii")
                    return f"data:image/png;base64,{b64}", None
                except requests.RequestException as e:
                    return None, f"Fetch image failed: {e}"
            return None, "Completed but no image URL in outcome"

        time.sleep(2)

    return None, "Image generation timed out (90s)"
