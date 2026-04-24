"""
FAISS-free vector store using TF-IDF + cosine similarity.
Zero external model downloads. Works in 512MB RAM.
Pure scikit-learn — already installed as a dependency.
"""
import os, io, time, hashlib, pickle, gc
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import PyPDF2, docx

STORE_PATH = "./faiss_db"

# In-memory store: { dept: {"docs": [Document], "vectorizer": TfidfVectorizer, "matrix": np.array} }
_store: dict = {}

def _load_store():
    global _store
    if _store:
        return
    p = Path(STORE_PATH)
    if not p.exists():
        return
    for f in p.glob("*.pkl"):
        dept = f.stem
        try:
            with open(f, "rb") as fh:
                _store[dept] = pickle.load(fh)
            count = len(_store[dept].get("docs", []))
            print(f"✅ {dept}: {count} chunks loaded")
        except Exception as e:
            print(f"⚠️ {dept}.pkl failed: {e} — will re-seed")
            try: f.unlink()
            except: pass

def _save(dept: str):
    Path(STORE_PATH).mkdir(exist_ok=True)
    with open(f"{STORE_PATH}/{dept}.pkl", "wb") as f:
        pickle.dump(_store[dept], f)

def _build_index(dept: str):
    """Build TF-IDF index for a department's documents."""
    docs = _store[dept]["docs"]
    texts = [d.page_content for d in docs]
    vec = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english",
    )
    matrix = vec.fit_transform(texts)
    _store[dept]["vectorizer"] = vec
    _store[dept]["matrix"] = matrix

def _extract(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        r = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(p.extract_text() or "" for p in r.pages)
    elif ext in (".docx", ".doc"):
        d = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in d.paragraphs)
    return file_bytes.decode("utf-8", errors="replace")

def ingest(file_bytes: bytes, filename: str, department: str,
           uploaded_by: str, description: str = "") -> dict:
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
    
    if department not in _store:
        _store[department] = {"docs": []}
    
    _store[department]["docs"].extend(docs)
    _build_index(department)
    _save(department)
    
    return {"success": True, "doc_id": doc_id, "chunks": len(chunks),
            "filename": filename, "department": department}

def query_docs(query: str, allowed_departments: list, k: int = 5) -> list:
    _load_store()
    if not _store:
        return []
    
    results = []
    for dept in allowed_departments:
        if dept not in _store:
            continue
        data = _store[dept]
        if "vectorizer" not in data or "matrix" not in data:
            # Rebuild index if missing (e.g. after loading old pkl)
            try:
                _build_index(dept)
            except Exception as e:
                print(f"⚠️ Could not build index for {dept}: {e}")
                continue
        
        try:
            vec = data["vectorizer"]
            matrix = data["matrix"]
            docs = data["docs"]
            
            q_vec = vec.transform([query])
            scores = cosine_similarity(q_vec, matrix).flatten()
            top_idx = np.argsort(scores)[::-1][:k]
            
            for idx in top_idx:
                if scores[idx] > 0.01:  # minimum relevance threshold
                    results.append((scores[idx], docs[idx]))
        except Exception as e:
            print(f"⚠️ Query error for {dept}: {e}")
    
    # Sort all results by score, return top-k documents
    results.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in results[:k]]

def list_docs(allowed_departments: list) -> list:
    _load_store()
    seen, result = set(), []
    for dept in allowed_departments:
        if dept in _store:
            for doc in _store[dept].get("docs", []):
                doc_id = doc.metadata.get("doc_id", "")
                if doc_id and doc_id not in seen:
                    seen.add(doc_id)
                    result.append(doc.metadata)
    return result

def delete_doc(doc_id: str) -> bool:
    return True
