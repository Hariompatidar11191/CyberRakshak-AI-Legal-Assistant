from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

import fitz
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "cybercrime-legal-kb").strip()

EMBED_MODEL = "@cf/baai/bge-m3"
VECTOR_SIZE = 1024
DATA_DIR = Path(os.getenv("LEGAL_RAG_DATA_DIR", "data/legal_documents"))
STORAGE_DIR = Path(os.getenv("LEGAL_RAG_STORAGE_DIR", "storage"))
MANIFEST_PATH = STORAGE_DIR / "qdrant_manifest.json"
CLOUDFLARE_API = "https://api.cloudflare.com/client/v4"


def require_config() -> None:
    required = {
        "CLOUDFLARE_ACCOUNT_ID": CLOUDFLARE_ACCOUNT_ID,
        "CLOUDFLARE_API_TOKEN": CLOUDFLARE_API_TOKEN,
        "QDRANT_URL": QDRANT_URL,
        "QDRANT_API_KEY": QDRANT_API_KEY,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing .env values: " + ", ".join(missing))


def qdrant() -> QdrantClient:
    require_config()
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)


def ensure_collection() -> None:
    client = qdrant()
    if not client.collection_exists(QDRANT_COLLECTION):
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    require_config()
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    endpoint = (
        f"{CLOUDFLARE_API}/accounts/{CLOUDFLARE_ACCOUNT_ID}"
        f"/ai/run/{EMBED_MODEL}"
    )
    all_vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        response = requests.post(
            endpoint,
            headers=headers,
            json={"text": batch},
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        if not body.get("success", False):
            raise RuntimeError(f"Cloudflare embedding error: {body.get('errors')}")
        result = body.get("result", {})
        vectors = result.get("data") or result.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(batch):
            raise RuntimeError(
                "Unexpected Cloudflare embedding response. "
                f"Result keys: {list(result.keys())}"
            )
        if any(len(v) != VECTOR_SIZE for v in vectors):
            raise RuntimeError(
                f"Expected {VECTOR_SIZE}-dimensional embeddings from {EMBED_MODEL}."
            )
        all_vectors.extend(vectors)
    return all_vectors


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest() -> dict:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        return {"files": {}}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    temp = MANIFEST_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(MANIFEST_PATH)


def extract(path: Path) -> list[Document]:
    source = str(path.resolve().relative_to(DATA_DIR.resolve()))
    docs = []
    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as pdf:
            for page_no, page in enumerate(pdf, 1):
                text = page.get_text("text").strip()
                if text:
                    docs.append(Document(
                        page_content=text,
                        metadata={"source": source, "file_name": path.name,
                                  "file_type": "pdf", "page": page_no},
                    ))
    elif path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            docs.append(Document(
                page_content=text,
                metadata={"source": source, "file_name": path.name,
                          "file_type": "txt", "page": 1},
            ))
    return docs


def chunk_pages(pages: list[Document], digest: str) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1400,
        chunk_overlap=200,
        add_start_index=True,
        separators=["\n\n", "\n", "।", ". ", "; ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    for n, chunk in enumerate(chunks):
        chunk.metadata["file_hash"] = digest
        chunk.metadata["chunk_no"] = n
    return chunks


def point_id(source: str, digest: str, chunk_no: int) -> str:
    # Qdrant accepts UUID or unsigned integer point IDs.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}|{digest}|{chunk_no}"))


def delete_ids(client: QdrantClient, ids: list[str]) -> None:
    if ids:
        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=models.PointIdsList(points=ids),
            wait=True,
        )


def ingest_directory() -> dict[str, Any]:
    require_config()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_collection()
    client = qdrant()
    manifest = load_manifest()
    files_manifest = manifest.setdefault("files", {})

    paths = sorted(
        p for p in DATA_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".txt"}
    )
    current = {
        str(p.resolve().relative_to(DATA_DIR.resolve())): p for p in paths
    }

    # Skip exact duplicate files by content hash.
    digest_to_source: dict[str, str] = {}
    duplicates = set()
    digests = {}
    for source, path in current.items():
        digest = file_hash(path)
        digests[source] = digest
        if digest in digest_to_source:
            duplicates.add(source)
        else:
            digest_to_source[digest] = source

    removed = set(files_manifest) - set(current)
    changed = []
    unchanged = 0
    for source, path in current.items():
        if source in duplicates:
            continue
        if files_manifest.get(source, {}).get("sha256") == digests[source]:
            unchanged += 1
        else:
            changed.append((source, path, digests[source]))

    chunks_uploaded = 0
    indexed_files = 0

    for source, path, digest in changed:
        chunks = chunk_pages(extract(path), digest)
        if not chunks:
            print(f"WARNING: No selectable text found in {source}; OCR may be needed.")
            continue

        vectors = embed_texts([c.page_content for c in chunks])
        points = []
        ids = []

        for n, (chunk, vector) in enumerate(zip(chunks, vectors)):
            pid = point_id(source, digest, n)
            ids.append(pid)
            payload = {
                "text": chunk.page_content,
                "source": source,
                "file_name": path.name,
                "file_type": path.suffix.lower().lstrip("."),
                "page": int(chunk.metadata.get("page", 1)),
                "chunk_no": n,
                "file_hash": digest,
            }
            points.append(models.PointStruct(id=pid, vector=vector, payload=payload))

        # Upload new points first; remove old points only after successful upsert.
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
            wait=True,
        )
        old_ids = files_manifest.get(source, {}).get("ids", [])
        delete_ids(client, old_ids)

        files_manifest[source] = {"sha256": digest, "ids": ids}
        save_manifest(manifest)
        indexed_files += 1
        chunks_uploaded += len(points)
        print(f"Indexed {source}: {len(points)} chunks")

    for source in removed | duplicates:
        delete_ids(client, files_manifest.get(source, {}).get("ids", []))
        files_manifest.pop(source, None)

    save_manifest(manifest)
    return {
        "files_found": len(paths),
        "exact_duplicates_skipped": len(duplicates),
        "files_indexed_or_updated": indexed_files,
        "unchanged_files_skipped": unchanged,
        "deleted_or_duplicate_entries_removed": len(removed | duplicates),
        "chunks_uploaded": chunks_uploaded,
        "qdrant_collection": QDRANT_COLLECTION,
    }


def search_legal_context(question: str, top_k: int = 6) -> list[Document]:
    require_config()
    ensure_collection()
    vector = embed_texts([question])[0]
    response = qdrant().query_points(
        collection_name=QDRANT_COLLECTION,
        query=vector,
        limit=max(1, min(top_k, 50)),
        with_payload=True,
    )
    docs = []
    for point in response.points:
        payload = point.payload or {}
        text = payload.get("text", "")
        if text:
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": payload.get("source", "Unknown"),
                    "file_name": payload.get("file_name", "Unknown"),
                    "page": payload.get("page"),
                    "chunk_no": payload.get("chunk_no"),
                    "score": point.score,
                },
            ))
    return docs


def format_context(docs: list[Document]) -> str:
    blocks = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown source")
        page = doc.metadata.get("page")
        citation = f"{source}, page {page}" if page else source
        blocks.append(f"[Source {i}: {citation}]\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)
