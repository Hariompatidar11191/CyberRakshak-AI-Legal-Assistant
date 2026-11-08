
import os
import requests
from dotenv import load_dotenv

load_dotenv()

account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
api_token = os.getenv("CLOUDFLARE_API_TOKEN")

url = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{account_id}/ai/run/@cf/baai/bge-m3"
)

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

payload = {
    "text": [
        "A victim has lost money due to UPI banking fraud.",
        "यूपीआई बैंकिंग धोखाधड़ी में पीड़ित के पैसे चोरी हो गए।"
    ]
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    print("HTTP Status:", response.status_code)

    response.raise_for_status()
    result = response.json()

    if result.get("success"):
        vectors = result["result"]["data"]

        print("Cloudflare embedding successful!")
        print("Number of embeddings:", len(vectors))
        print("Embedding dimensions:", len(vectors[0]))

    else:
        print("API Error:", result.get("errors"))

except Exception as e:
    print("ERROR:", e)
