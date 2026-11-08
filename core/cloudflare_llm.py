
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

MODEL = os.getenv(
    "CLOUDFLARE_LLM_MODEL",
    "@cf/zai-org/glm-4.7-flash"
)

API_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{ACCOUNT_ID}/ai/v1/chat/completions"
)



def generate_response(messages, temperature=0.2, max_tokens=1200):
    """Generate a response using Cloudflare Workers AI."""

    if not ACCOUNT_ID or not API_TOKEN:
        raise ValueError("Cloudflare credentials are missing.")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }


    payload = {
    "model": MODEL,
    "messages": messages,
    "temperature": 0.2,

    # Reserve tokens for the actual answer
    "max_completion_tokens": 1500,

    # Disable lengthy reasoning for normal chat
    "chat_template_kwargs": {
        "enable_thinking": False,
        "clear_thinking": True
    },

    "stream": False
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=90
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Cloudflare API error {response.status_code}: "
            f"{response.text[:1000]}"
        )

    result = response.json()

    choices = result.get("choices", [])

    if not choices:
        raise RuntimeError(
            f"No response choices returned: {result}"
        )

    message = choices[0].get("message", {})
    content = message.get("content")

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
        )

    if not isinstance(content, str) or not content.strip():
        finish_reason = choices[0].get("finish_reason")

        raise RuntimeError(
            f"No final answer returned. "
            f"Finish reason: {finish_reason}. "
            f"Please retry."
        )

    return content.strip()