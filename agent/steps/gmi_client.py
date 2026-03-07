import os

from google import genai

# LLM inference (infer_vibe, generate_html, nudge)
GMI_LLM_MODEL = "gemini-3.1-pro"
# Image generation (future use)
GMI_IMAGE_MODEL = "gemini-3-pro-image-preview"

# Backward-compat alias for LLM steps
GMI_MODEL = GMI_LLM_MODEL

def get_gmi_client(model_id: str = None):
    """Returns a GMI client. Uses GMI_LLM_MODEL by default."""
    model = model_id or GMI_LLM_MODEL
    return genai.Client(
        vertexai=True,
        http_options={
            "base_url": f"https://api.gmi-serving.com/v1/models/{model}:generateContent",
            "headers": {
                "Authorization": f"Bearer {os.environ['GMI_API_KEY']}"
            }
        }
    )

def get_gmi_image_client():
    """Returns a GMI client configured for image generation."""
    return get_gmi_client(GMI_IMAGE_MODEL)
