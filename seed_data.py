"""Run once: python seed_data.py"""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app.core.vectorstore import ingest
from pathlib import Path

DOCS = [
    ("resources/employee_handbook.txt",      "general",     "Company-wide employee handbook 2024"),
    ("resources/hr_confidential.txt",         "hr",          "HR policies, salary bands, attrition data"),
    ("resources/finance_q3_report.txt",       "finance",     "Q3 FY25 financial report"),
    ("resources/engineering_guidelines.txt",  "engineering", "Tech stack, dev standards, incident mgmt"),
]

print("\n🚀 NexusAI — Seeding FAISS Vector Store\n" + "─"*50)
for path, dept, desc in DOCS:
    p = Path(path)
    if not p.exists():
        print(f"  ⚠  Not found: {path}"); continue
    print(f"  📄 {p.name} → [{dept}]", end="  ")
    r = ingest(p.read_bytes(), p.name, dept, "system@nexus.ai", desc)
    print(f"✅ {r['chunks']} chunks" if r["success"] else f"❌ {r['reason']}")

print("\n" + "─"*50)
print("✅ Done! Start backend:\n\n  uvicorn app.main:app --reload\n")
