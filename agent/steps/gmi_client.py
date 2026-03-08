import base64
import os
import json
from typing import Optional

import requests

GMI_BASE_URL = "https://api.gmi-serving.com/v1"
GMI_LLM_MODEL = "google/gemini-3.1-pro-preview"
GMI_FAST_MODEL = "google/gemini-3-flash-preview"
GMI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# GMI image API: try OpenAI-compatible /v1/images/generations first
GMI_IMAGE_URL = "https://api.gmi-serving.com/v1/images/generations"

GMI_MODEL = GMI_LLM_MODEL


class _GmiResponse:
    """Minimal response wrapper matching the interface used by infer_vibe / generate_html / nudge."""
    def __init__(self, text: str):
        self.text = text


class _GmiModels:
    """Wraps GMI Cloud's /v1/chat/completions as a .models.generate_content() interface."""

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
    """Lightweight client exposing .models.generate_content() backed by GMI Cloud REST API."""

    def __init__(self, api_key: str):
        self.models = _GmiModels(api_key)


def get_gmi_client(model_id: str = None):
    """Returns a GMI Cloud client."""
    return _GmiClient(api_key=os.environ["GMI_API_KEY"])


def get_gmi_image_client():
    """Returns a GMI client configured for image generation."""
    return get_gmi_client(GMI_IMAGE_MODEL)


def generate_image(
    prompt: str,
    aspect_ratio: str = "4:3",
    resolution: str = "1K",
    model: str = GMI_IMAGE_MODEL,
) -> Optional[str]:
    """
    Generate an image via GMI Cloud image API (gemini-3.1-flash-image-preview).
    Returns base64 data URI (data:image/png;base64,...) or None on failure.
    """
    api_key = os.environ.get("GMI_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.post(
            GMI_IMAGE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data") or []
        if not items:
            return None
        img = items[0]
        b64 = img.get("b64_json")
        url = img.get("url")
        mime = img.get("mime_type", "image/png")
        if b64:
            return f"data:{mime};base64,{b64}"
        if url:
            # Fetch and convert to base64 for embedding in single-file HTML
            img_resp = requests.get(url, timeout=30)
            img_resp.raise_for_status()
            b64 = base64.b64encode(img_resp.content).decode("ascii")
            return f"data:{mime};base64,{b64}"
        return None
    except Exception:
        return None
