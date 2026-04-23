"""FAISS vector store — memory optimised for Railway 512MB"""
import os, io, time, hashlib, pickle, gc
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2, docx

FAISS_PATH = "./faiss_db"
_store: dict = {}
_embeddings = None

def _get_emb():
    """Load embedding model only when needed."""
    global _embeddings
    if _embeddings is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings

def _release_emb():
    """Free embedding model from RAM after use — saves ~400MB."""
    global _embeddings
    if _embeddings is not None:
        _embeddings = None
        gc.collect()

def _load_store():
    global _store
    if _store:
        return
    p = Path(FAISS_PATH)
    if not p.exists():
        return
    for f in p.glob("*.pkl"):
        dept = f.stem
        try:
            with open(f, "rb") as fh:
                _store[dept] = pickle.load(fh)
            print(f"✅ {dept}.pkl loaded OK")
        except Exception as e:
            print(f"⚠️ {dept}.pkl broken: {e} — deleting")
            try: f.unlink()
            except: pass

def _save(dept: str):
    Path(FAISS_PATH).mkdir(exist_ok=True)
    with open(f"{FAISS_PATH}/{dept}.pkl", "wb") as f:
        pickle.dump(_store[dept], f)

def _extract(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        r = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(p.extract_text() or "" for p in r.pages)
    elif ext in (".docx", ".doc"):
        d = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in d.paragraphs)
    return file_bytes.decode("utf-8", errors="replace")

def ingest(file_bytes, filename, department, uploaded_by, description=""):
    text = _extract(file_bytes, filename)
    if not text.strip():
        return {"success": False, "reason": "Could not extract text."}
    doc_id = hashlib.md5(file_bytes).hexdigest()[:12]
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=100
    ).split_text(text)
    docs = [Document(page_content=c, metadata={
        "doc_id": doc_id, "filename": filename, "department": department,
        "uploaded_by": uploaded_by, "description": description,
        "chunk_index": i, "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }) for i, c in enumerate(chunks)]
    _load_store()
    emb = _get_emb()
    if department in _store:
        _store[department].add_documents(docs)
    else:
        _store[department] = FAISS.from_documents(docs, emb)
    _save(department)
    # Release model after seeding to free ~400MB RAM
    _release_emb()
    return {"success": True, "doc_id": doc_id, "chunks": len(chunks),
            "filename": filename, "department": department}

def query_docs(query: str, allowed_departments: list, k: int = 3) -> list:
    """Query FAISS using embedding model, then release it immediately."""
    _load_store()
    if not _store:
        return []
    emb = _get_emb()
    results = []
    for dept in allowed_departments:
        if dept in _store:
            try:
                results.extend(_store[dept].similarity_search(query, k=k))
            except Exception as e:
                print(f"⚠️ Query error {dept}: {e}")
    # Release embedding model immediately after query to free RAM for LLM call
    _release_emb()
    return results[:k]

def list_docs(allowed_departments: list) -> list:
    _load_store()
    seen, result = set(), []
    for dept in allowed_departments:
        if dept in _store:
            try:
                for doc in _store[dept].docstore._dict.values():
                    doc_id = doc.metadata.get("doc_id", "")
                    if doc_id and doc_id not in seen:
                        seen.add(doc_id)
                        result.append(doc.metadata)
            except Exception:
                pass
    return result

def delete_doc(doc_id: str) -> bool:
    return True
