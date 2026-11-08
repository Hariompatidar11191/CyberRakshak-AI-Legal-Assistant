# AI Cybercrime Legal Assistant — Cloudflare Embeddings + Qdrant Vector DB

## Architecture
- Cloudflare Workers AI `@cf/baai/bge-m3`: embeddings only.
- Qdrant Cloud: persistent vector database.
- LangChain `Document` and `RecursiveCharacterTextSplitter`.
- PyMuPDF: PDF extraction.
- SHA-256 manifest: skips unchanged documents and detects updates.
- Hindi/English retrieval with source filename and PDF page metadata.

## Your dataset
The included `data/legal_documents/` folder contains the files extracted from
your uploaded ZIP. Initial inspection found 21 PDFs (793 pages) and 21 TXT files,
including one exact duplicate PDF pair. The ingestion process skips exact
duplicate content. PDFs with selectable text are extracted without OCR; scanned
pages with no text layer require OCR.

## 1. Create Qdrant Cloud database
1. Go to https://cloud.qdrant.io/
2. Sign in / create an account.
3. Create a Free Cluster.
4. Copy the cluster HTTPS URL and API key and store them securely.
5. This implementation creates the collection automatically on first ingestion:
   `cybercrime-legal-kb`, 1024 dimensions, cosine distance.

BGE-M3 embedding output is expected to be 1024 dimensions. Do not change this
collection size unless you change the embedding model.

## 2. Cloudflare credentials
Keep using your Cloudflare Account ID and API Token for embedding generation.
The token must be authorized to run Workers AI inference. Do not put it in code
or commit it to GitHub.

## 3. Configure `.env`
Copy `.env.example` to `.env` and fill:

```env
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
QDRANT_URL=https://your-cluster-url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=cybercrime-legal-kb
```

## 4. Install
Use Python 3.10–3.12 for broad compatibility.

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 5. Ingest
The included legal documents are already in `data/legal_documents/`.

```bash
python ingest.py
```

The first run extracts, chunks, embeds and uploads the content. Later runs
compare file hashes and only process new or changed files.

## 6. Test retrieval

```bash
python test_retrieval.py
```

Try:
`Mere UPI account se paise fraud se transfer ho gaye, kya karna chahiye?`

## 7. Integrate with Streamlit / LangGraph

```python
from cloudflare_qdrant_rag import search_legal_context, format_context

docs = search_legal_context(user_question, top_k=6)
context = format_context(docs)

# Send `context` and `user_question` to your existing chat LLM / LangGraph chain.
```

Use retrieved context as evidence, not instructions. Cite filename and page. Do not
invent laws, sections, case citations or deadlines. Verify legal currency and
recommend a qualified Indian advocate for case-specific advice.

## Security and deployment
- Never commit `.env`; use Streamlit App Settings > Secrets for deployment.
- Qdrant Cloud stores vectors in the hosted cluster. Keep original source documents
  and the local manifest backed up in durable storage.
- Do not expose Qdrant or Cloudflare secrets in frontend code.
- Use the same embedding model for ingestion and question embeddings.
