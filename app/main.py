"""NexusAI FastAPI backend — production ready"""
import os, threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# ── LangSmith ─────────────────────────────────────────────────────
if settings.langchain_api_key and len(settings.langchain_api_key) > 20:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]     = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"]     = settings.langchain_project
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.api import auth_router, chat_router, docs_router, oauth_router

app = FastAPI(title="NexusAI API", version="2.0.0", docs_url="/docs")

# ── CORS — wildcard for Render free tier compatibility ─────────────
# JWT uses Authorization: Bearer (not cookies) so credentials=False is correct
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
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

# ── Health/ping endpoints ──────────────────────────────────────────
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
    """Lightweight ping — use this to wake up Render before sending chat requests."""
    return {"pong": True}
