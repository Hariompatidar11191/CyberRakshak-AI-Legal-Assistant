
from cloudflare_qdrant_rag import (
    search_legal_context,
    format_context
)


def retrieve_legal_information(question: str, top_k: int = 6):
    """
    Retrieve relevant Indian cybercrime and banking laws
    from the existing Qdrant knowledge base.
    """

    if not question or not question.strip():
        return [], ""

    documents = search_legal_context(
        question=question.strip(),
        top_k=top_k
    )

    context = format_context(documents)

    return documents, context


def get_legal_sources(documents):
    """
    Extract source information from retrieved documents.
    """

    sources = []

    for doc in documents:
        metadata = doc.metadata or {}

        source = {
            "file_name": metadata.get("file_name")
            or metadata.get("source", "Unknown"),

            "page": metadata.get("page", "N/A")
        }

        if source not in sources:
            sources.append(source)

    return sources
