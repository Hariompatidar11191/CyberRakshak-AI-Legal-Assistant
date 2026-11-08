from cloudflare_qdrant_rag import search_legal_context, format_context

if __name__ == '__main__':
    q = input('Ask a legal question (Hindi/English): ').strip()
    print(format_context(search_legal_context(q, top_k=6)))
