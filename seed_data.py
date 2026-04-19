"""
Auto-seeds FAISS vector store on startup.
Skips if already seeded (faiss_db folder exists with data).
"""
import sys, os
from pathlib import Path

sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app.core.vectorstore import ingest

# ✅ Correct path — must match FAISS_PATH in vectorstore.py
FAISS_DB_PATH = Path("faiss_db")

# Check if already seeded (any .pkl file exists)
existing = list(FAISS_DB_PATH.glob("*.pkl")) if FAISS_DB_PATH.exists() else []
if existing:
    print(f"✅ FAISS already seeded ({len(existing)} departments). Skipping...")
    sys.exit(0)

DOCS = [
    ("resources/employee_handbook.txt",     "general",     "Company-wide employee handbook 2024"),
    ("resources/hr_confidential.txt",        "hr",          "HR policies, salary bands, attrition data"),
    ("resources/finance_q3_report.txt",      "finance",     "Q3 FY25 financial report"),
    ("resources/engineering_guidelines.txt", "engineering", "Tech stack, dev standards, incident mgmt"),
]

print("\n🚀 NexusAI — Seeding FAISS Vector Store\n" + "─"*50)
success_count = 0
for path, dept, desc in DOCS:
    p = Path(path)
    if not p.exists():
        print(f"  ⚠  Not found: {path}")
        continue
    print(f"  📄 {p.name} → [{dept}]", end="  ", flush=True)
    try:
        r = ingest(p.read_bytes(), p.name, dept, "system@nexus.ai", desc)
        if r["success"]:
            print(f"✅ {r['chunks']} chunks")
            success_count += 1
        else:
            print(f"❌ {r['reason']}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "─"*50)
print(f"✅ Seeded {success_count}/4 departments successfully!")
