"""NexusAI FastAPI backend"""
import os, threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings

# Disable LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.api import auth_router, chat_router, docs_router, oauth_router

app = FastAPI(title="NexusAI API", version="2.0.0", docs_url="/docs")

# ── CORS — must be FIRST middleware, before everything else ────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

app.include_router(auth_router.router,  prefix="/api")
app.include_router(chat_router.router,  prefix="/api")
app.include_router(docs_router.router,  prefix="/api")
app.include_router(oauth_router.router, prefix="/api")

# ── Auto-seed on startup ───────────────────────────────────────────
def _run_seed():
    try:
        from pathlib import Path
        faiss_db = Path("faiss_db")
        pkl_files = list(faiss_db.glob("*.pkl")) if faiss_db.exists() else []
        if pkl_files:
            print(f"✅ FAISS already seeded ({len(pkl_files)} depts). Skipping.")
            return
        print("🌱 Seeding FAISS...")
        import runpy
        runpy.run_path("seed_data.py", run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:
        print(f"⚠ Seed error: {e}")

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=_run_seed, daemon=True).start()

@app.get("/")
def root():
    from pathlib import Path
    faiss_db = Path("faiss_db")
    seeded = [f.stem for f in faiss_db.glob("*.pkl")] if faiss_db.exists() else []
    return {
        "status": "ok",
        "service": "NexusAI API v2.0",
        "groq_configured": bool(settings.groq_api_key_70b or settings.groq_api_key_8b),
        "seeded_departments": seeded,
        "cors": "wildcard",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ping")
def ping():
    return {"pong": True}