"""NexusAI FastAPI backend"""
import os, threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings

os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.api import auth_router, chat_router, docs_router, oauth_router

app = FastAPI(title="NexusAI API", version="2.0.0", docs_url="/docs")

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

def _run_seed():
    """Delete incompatible pkl files, then seed fresh from resource txt files."""
    try:
        from pathlib import Path
        faiss_db = Path("faiss_db")
        expected = {"general", "hr", "finance", "engineering"}

        # Check which departments are actually loadable
        good = set()
        if faiss_db.exists():
            for pkl in faiss_db.glob("*.pkl"):
                try:
                    import pickle
                    with open(pkl, "rb") as f:
                        obj = pickle.load(f)
                    good.add(pkl.stem)
                    print(f"✅ {pkl.stem}.pkl loaded OK")
                except Exception as e:
                    print(f"⚠️ {pkl.stem}.pkl broken ({e}) — deleting for re-seed")
                    pkl.unlink()

        missing = expected - good
        if not missing:
            print(f"✅ All 4 departments loaded from pkl. No seeding needed.")
            return

        print(f"🌱 Missing departments: {missing} — seeding now...")
        import runpy
        runpy.run_path("seed_data.py", run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:
        print(f"⚠ Startup seed error: {e}")
        import traceback; traceback.print_exc()

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
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ping")
def ping():
    return {"pong": True}
