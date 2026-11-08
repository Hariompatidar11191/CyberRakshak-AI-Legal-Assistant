
from core.rag_engine import (
    retrieve_legal_information,
    get_legal_sources
)

question = """
What should a victim do after losing money
in a UPI banking fraud in India?
"""

try:
    documents, context = retrieve_legal_information(
        question,
        top_k=6
    )

    print("\nRETRIEVED DOCUMENTS:", len(documents))

    print("\nLEGAL CONTEXT:\n")
    print(context)

    print("\nSOURCES:\n")
    for source in get_legal_sources(documents):
        print(source)

except Exception as e:
    print("ERROR:", e)
