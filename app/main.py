"""NexusAI FastAPI backend — production ready"""
import os, sys, threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# ── LangSmith: only enable if key is real ──────────────────────────
if settings.langchain_api_key and len(settings.langchain_api_key) > 10:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.api import auth_router, chat_router, docs_router, oauth_router

app = FastAPI(title="NexusAI API", version="2.0.0", docs_url="/docs")

# ── CORS — allow Vercel + localhost ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nexusai-frontend-nine.vercel.app",  # ✅ your frontend
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router,  prefix="/api")
app.include_router(chat_router.router,  prefix="/api")
app.include_router(docs_router.router,  prefix="/api")
app.include_router(oauth_router.router, prefix="/api")

# ── Auto-seed FAISS on startup (safe: skips if already done) ───────
def _run_seed():
    try:
        from pathlib import Path
        faiss_db = Path("faiss_db")
        existing = list(faiss_db.glob("*.pkl")) if faiss_db.exists() else []
        if existing:
            print(f"✅ FAISS already has {len(existing)} dept(s) indexed. Skipping seed.")
            return
        print("🌱 Seeding FAISS vector store...")
        # Run seed_data.py as a module
        import runpy
        runpy.run_path("seed_data.py", run_name="__main__")
    except SystemExit:
        pass  # seed_data.py calls sys.exit(0) on skip — that's fine
    except Exception as e:
        print(f"⚠ Seed warning: {e}")

@app.on_event("startup")
async def startup_event():
    # Run in background thread so server starts immediately
    threading.Thread(target=_run_seed, daemon=True).start()

@app.get("/")
def root():
    from pathlib import Path
    faiss_db = Path("faiss_db")
    seeded_depts = [f.stem for f in faiss_db.glob("*.pkl")] if faiss_db.exists() else []
    return {
        "status": "ok",
        "service": "NexusAI API v2.0",
        "groq_configured": bool(settings.groq_api_key_70b or settings.groq_api_key_8b),
        "seeded_departments": seeded_depts,
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "healthy", "environment": settings.environment}
