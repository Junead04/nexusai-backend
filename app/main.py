"""NexusAI FastAPI backend"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth_router, chat_router, docs_router
from app.api import oauth_router

# Only enable LangSmith if key is actually configured
if settings.langchain_api_key and not settings.langchain_api_key.startswith("ls__your"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

app = FastAPI(title="NexusAI API", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router,  prefix="/api")
app.include_router(chat_router.router,  prefix="/api")
app.include_router(docs_router.router,  prefix="/api")
app.include_router(oauth_router.router, prefix="/api")

@app.get("/")
def root():
    groq_ok = bool(settings.groq_api_key_70b or settings.groq_api_key_8b)
    return {
        "status": "ok",
        "service": "NexusAI API v2.0",
        "groq_configured": groq_ok,
        "oauth_configured": bool(settings.google_client_id),
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "healthy", "environment": settings.environment}

import subprocess
import sys
import os

@app.on_event("startup")
def seed_data():
    try:
        subprocess.run(
            [sys.executable, os.path.join(os.getcwd(), "seed_data.py")],
            check=True
        )
        print("✅ Seed data loaded")
    except Exception as e:
        print("❌ Seed failed:", e)
