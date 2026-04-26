# NexusAI Backend

> Enterprise RAG Knowledge System — FastAPI Backend

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://langchain.com)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA-orange)](https://console.groq.com)
[![Railway](https://img.shields.io/badge/Deployed-Railway-blueviolet)](https://railway.app)

**Live API:** https://nexusai-backend-production-f2e2.up.railway.app  
**Frontend:** https://github.com/Junead04/nexusai-frontend  
**Live App:** https://nexusai-frontend-nine.vercel.app

---

## What is NexusAI?

NexusAI is a full-stack enterprise RAG (Retrieval-Augmented Generation) system. Employees ask questions in natural language and get AI-generated answers grounded in real company documents — with role-based access control ensuring each user only sees what they're authorised to see.

---

## Features

- **RAG Pipeline** — TF-IDF vector store retrieves relevant document chunks before LLM generation. Answers are always grounded in real documents, never hallucinated.
- **Role-Based Access Control** — 6 roles (Admin, HR Manager, Finance Analyst, Marketing Manager, Engineer, Employee). Each role only queries departments they have access to.
- **Dual LLM Routing** — Simple queries use LLaMA 3.1 8B (fast). Complex or financial queries automatically route to LLaMA 3.3 70B (more capable).
- **Google OAuth** — Single sign-on via Google account.
- **PII Guardrails** — Sensitive information is sanitised before sending to the LLM.
- **Auto-seeding** — On first startup, the system automatically indexes all resource documents.
- **Multi-language Support** — Works with English, Hindi, and Tamil queries.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| LLM | Groq API (LLaMA 3.1 8B + 3.3 70B) |
| Orchestration | LangChain 0.3 |
| Vector Search | TF-IDF (scikit-learn) |
| Auth | JWT + Google OAuth 2.0 |
| Deployment | Railway |

---

## Project Structure

```
nexusai-backend/
├── app/
│   ├── api/
│   │   ├── auth_router.py      # Login, JWT, demo users
│   │   ├── chat_router.py      # /api/chat/ask endpoint
│   │   ├── docs_router.py      # Document upload & list
│   │   └── oauth_router.py     # Google OAuth flow
│   ├── core/
│   │   ├── config.py           # Settings from env vars
│   │   ├── rag_engine.py       # LLM routing + answer generation
│   │   ├── vectorstore.py      # TF-IDF indexing + search
│   │   ├── rbac.py             # Role-based access logic
│   │   ├── auth.py             # JWT creation + verification
│   │   └── guardrails.py       # Query validation + PII filtering
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   └── main.py                 # FastAPI app + CORS + startup
├── resources/                  # Seed documents (txt files)
├── faiss_db/                   # TF-IDF index store (auto-created)
├── seed_data.py                # Seeds vector store on startup
├── requirements.txt
├── Dockerfile
└── railway.json
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/Junead04/nexusai-backend.git
cd nexusai-backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux

# 5. Add your Groq API key to .env
# GROQ_API_KEY_70B=gsk_your_key_here
# GROQ_API_KEY_8B=gsk_your_key_here

# 6. Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Environment Variables

Create a `.env` file with the following:

```env
# Required — get free key at console.groq.com
GROQ_API_KEY_70B=gsk_your_key_here
GROQ_API_KEY_8B=gsk_your_key_here

# JWT Security
SECRET_KEY=your-secret-key-here

# URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

ENVIRONMENT=development

# Optional — Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Optional — LangSmith monitoring (leave blank to disable)
LANGCHAIN_API_KEY=
```

---

## Demo Accounts

| Email | Password | Role | Access |
|---|---|---|---|
| admin@nexus.ai | admin123 | Administrator | All departments |
| hr@nexus.ai | hr123 | HR Manager | HR + General |
| finance@nexus.ai | finance123 | Finance Analyst | Finance + General |
| marketing@nexus.ai | marketing123 | Marketing Manager | Marketing + General |
| dev@nexus.ai | dev123 | Engineer | Engineering + General |
| emp@nexus.ai | emp123 | Employee | General only |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check + seeded departments |
| GET | `/ping` | Lightweight ping |
| POST | `/api/auth/login` | Email/password login |
| GET | `/api/auth/demo-users` | List demo accounts |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/chat/ask` | Ask a question (RAG) |
| GET | `/api/documents/list` | List indexed documents |
| POST | `/api/documents/upload` | Upload new document |
| GET | `/api/auth/google` | Start Google OAuth |
| GET | `/api/auth/google/callback` | Google OAuth callback |

---

## Deployment on Railway

```bash
# 1. Push to GitHub
git push origin main

# 2. Connect Railway to this repo at railway.app

# 3. Add environment variables in Railway dashboard

# 4. Railway auto-deploys on every push
```

Required Railway environment variables:
```
GROQ_API_KEY_70B
GROQ_API_KEY_8B
SECRET_KEY
ENVIRONMENT=production
FRONTEND_URL=https://your-vercel-url.vercel.app
BACKEND_URL=https://your-railway-url.up.railway.app
```

---

## How RAG Works

```
User Question
     ↓
Guardrails Check (PII, harmful content)
     ↓
RBAC Filter (which departments can this user access?)
     ↓
TF-IDF Search (find relevant document chunks)
     ↓
LLM Routing (simple → 8B model, complex → 70B model)
     ↓
Groq API Call (LLaMA generates grounded answer)
     ↓
Response with sources cited
```

---

## Author

**Junead** — [GitHub](https://github.com/Junead04) · [LinkedIn](https://linkedin.com/in/junead04)

---

## License

MIT License — free to use and modify.
