"""
RAG Engine — NexusAI
Fast on Render free tier: timeouts set, reduced tokens, 8B always used for speed.
"""
import time, re
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings, get_groq_key
from app.core.vectorstore import query_docs
from app.core.guardrails import validate, sanitize
from app.core.rbac import get_departments

# Only use these patterns for complex routing
_COMPLEX = [
    r"(?i)\b(revenue|profit|ebitda|margin|balance sheet|p&l|cashflow|valuation)\b",
    r"(?i)\b(analyze|forecast|predict|calculate)\b",
]

def _is_complex(q: str) -> bool:
    return any(re.search(p, q) for p in _COMPLEX)

def _llm(use_complex: bool) -> ChatGroq:
    key = get_groq_key()
    # On free Render: always use 8B for reliability, 70B only for explicit finance queries
    model = settings.model_complex if use_complex else settings.model_simple
    return ChatGroq(
        api_key=key,
        model=model,
        temperature=0.1,
        max_tokens=800,          # Keep short = faster response
        request_timeout=20,      # 20s hard timeout — Render limit is 30s
    )

_SYSTEM = """You are NexusAI, an enterprise knowledge assistant.
Answer ONLY from the CONTEXT below. Be concise (max 300 words).
If context is insufficient, say: "I don't have enough information in the available documents."
Cite the source document name.

CONTEXT:
{context}

User Role: {role} | Departments: {departments}"""

def ask(query: str, role: str) -> dict:
    start = time.time()

    # Guardrails
    ok, reason, clean = validate(query)
    if not ok:
        return {"answer": f"⚠️ {reason}", "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": True,
                "model_used": "none", "is_complex": False}

    # RBAC retrieval
    departments = get_departments(role)
    docs = query_docs(clean, departments, k=3)  # k=3 instead of 5 — faster
    if not docs:
        return {"answer": "📭 No relevant documents found. The knowledge base may still be loading — try again in 30 seconds.",
                "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": False,
                "model_used": "none", "is_complex": False}

    use_complex = _is_complex(query)
    model_name = settings.model_complex if use_complex else settings.model_simple

    context = "\n\n---\n\n".join(
        f"[{d.metadata.get('filename')} | {d.metadata.get('department','').upper()}]\n{d.page_content}"
        for d in docs
    )
    prompt = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", "{question}")])

    try:
        response = (prompt | _llm(use_complex)).invoke({
            "context": context, "role": role,
            "departments": ", ".join(departments), "question": clean,
        })
    except ValueError as e:
        return {"answer": f"⚙️ Config error: {str(e)}", "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": True,
                "model_used": "none", "is_complex": False}
    except Exception as e:
        err = str(e)
        if "invalid_api_key" in err or "401" in err:
            return {"answer": "🔑 Invalid GROQ API key. Check your Render environment variables.",
                    "sources": [], "tokens": 0, "cost": 0.0,
                    "latency": round(time.time()-start, 2), "blocked": True,
                    "model_used": "none", "is_complex": False}
        if "timeout" in err.lower() or "502" in err or "timed" in err.lower():
            return {"answer": "⏱️ Request timed out. Render free tier has a 30s limit. Try a shorter question or wait a moment.",
                    "sources": [], "tokens": 0, "cost": 0.0,
                    "latency": round(time.time()-start, 2), "blocked": True,
                    "model_used": "none", "is_complex": False}
        return {"answer": f"❌ Error: {err[:150]}", "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": True,
                "model_used": "none", "is_complex": False}

    answer = sanitize(response.content)
    usage  = getattr(response, "usage_metadata", {}) or {}
    total_tokens = (usage.get("total_tokens") if isinstance(usage, dict) else None) or len(answer.split()) * 2
    cost = (total_tokens / 1000) * (0.00059 if use_complex else 0.00006)

    seen, sources = set(), []
    for doc in docs:
        fn = doc.metadata.get("filename", "Unknown")
        if fn not in seen:
            seen.add(fn)
            sources.append({"filename": fn,
                            "department": doc.metadata.get("department", "general"),
                            "preview": doc.page_content[:100] + "..."})

    return {"answer": answer, "sources": sources, "tokens": total_tokens, "cost": cost,
            "latency": round(time.time()-start, 2), "blocked": False,
            "model_used": model_name, "is_complex": use_complex}
