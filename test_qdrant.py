
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import os

load_dotenv()

try:
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30
    )

    result = client.get_collections()

    print("SUCCESS: Connected to Qdrant!")

    for collection in result.collections:
        print("Collection:", collection.name)

except Exception as e:
    print("CONNECTION ERROR:", e)
