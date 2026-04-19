"""
RAG Engine — NexusAI
Simple Q&A  → LLaMA 3.1 8B  (fast)
Complex/financial → LLaMA 3.3 70B (smarter)
Both free on Groq Cloud.
"""
import time, re
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings, get_groq_key
from app.core.vectorstore import query_docs
from app.core.guardrails import validate, sanitize
from app.core.rbac import get_departments

_COMPLEX = [
    r"(?i)\b(analyze|analyse|compare|summarize|explain|calculate|forecast|predict)\b",
    r"(?i)\b(revenue|profit|ebitda|margin|balance sheet|p&l|cashflow|valuation)\b",
    r"(?i)\b(why|how does|what caused|impact of|reason for)\b",
    r"(?i)\b(all departments|across|overview|comprehensive|detailed report)\b",
]

def _is_complex(q: str) -> bool:
    return any(re.search(p, q) for p in _COMPLEX)

def _llm(use_complex: bool) -> ChatGroq:
    key = get_groq_key()
    model = settings.model_complex if use_complex else settings.model_simple
    return ChatGroq(api_key=key, model=model, temperature=0.1, max_tokens=2048)

_SYSTEM = """You are NexusAI, an intelligent enterprise knowledge assistant.
Answer ONLY from the CONTEXT provided. Do not use outside knowledge.
If context is insufficient, say: "I don't have enough information in the available documents."
Always cite the source document name. Be professional and concise.

CONTEXT:
{context}

User Role: {role} | Accessible Departments: {departments}"""

def ask(query: str, role: str) -> dict:
    start = time.time()

    # Guardrails check
    ok, reason, clean = validate(query)
    if not ok:
        return {"answer": f"⚠️ {reason}", "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": True, "model_used": "none", "is_complex": False}

    # RBAC document retrieval
    departments = get_departments(role)
    docs = query_docs(clean, departments, k=5)
    if not docs:
        return {"answer": "📭 No relevant documents found. Make sure seed_data.py was run and documents are uploaded.",
                "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": False, "model_used": "none", "is_complex": False}

    use_complex = _is_complex(query)
    model_name = settings.model_complex if use_complex else settings.model_simple
    context = "\n\n---\n\n".join(
        f"[Source {i+1} | {d.metadata.get('filename')} | {d.metadata.get('department','').upper()}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )
    prompt = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", "{question}")])

    try:
        response = (prompt | _llm(use_complex)).invoke({
            "context": context, "role": role,
            "departments": ", ".join(departments), "question": clean,
        })
    except ValueError as e:
        return {"answer": f"⚙️ Configuration error: {str(e)}", "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": True, "model_used": "none", "is_complex": False}
    except Exception as e:
        err = str(e)
        if "invalid_api_key" in err or "401" in err:
            return {"answer": "🔑 Invalid GROQ API Key. Open backend/.env and replace GROQ_API_KEY_70B with your real key from console.groq.com, then restart the backend.",
                    "sources": [], "tokens": 0, "cost": 0.0,
                    "latency": round(time.time()-start, 2), "blocked": True, "model_used": "none", "is_complex": False}
        return {"answer": f"❌ Error: {err[:200]}", "sources": [], "tokens": 0, "cost": 0.0,
                "latency": round(time.time()-start, 2), "blocked": True, "model_used": "none", "is_complex": False}

    answer = sanitize(response.content)
    usage = getattr(response, "usage_metadata", {}) or {}
    total_tokens = (usage.get("total_tokens") if isinstance(usage, dict) else None) or len(answer.split()) * 2
    cost = (total_tokens / 1000) * (0.00059 if use_complex else 0.00006)

    seen, sources = set(), []
    for doc in docs:
        fn = doc.metadata.get("filename", "Unknown")
        if fn not in seen:
            seen.add(fn)
            sources.append({"filename": fn, "department": doc.metadata.get("department", "general"),
                            "preview": doc.page_content[:120] + "..."})
    return {"answer": answer, "sources": sources, "tokens": total_tokens, "cost": cost,
            "latency": round(time.time()-start, 2), "blocked": False,
            "model_used": model_name, "is_complex": use_complex}
