"""
Seeds FAISS vector store from resource txt files.
Runs on startup — skips departments that already have valid pkl files.
"""
import sys, os
from pathlib import Path

sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app.core.vectorstore import ingest, _get_emb

FAISS_DB = Path("faiss_db")
FAISS_DB.mkdir(exist_ok=True)

DOCS = [
    ("resources/employee_handbook.txt",     "general",     "Company-wide employee handbook 2024"),
    ("resources/hr_confidential.txt",        "hr",          "HR policies, salary bands, attrition data"),
    ("resources/finance_q3_report.txt",      "finance",     "Q3 FY25 financial report"),
    ("resources/engineering_guidelines.txt", "engineering", "Tech stack, dev standards, incident mgmt"),
]

# Pre-load the embedding model once (avoids repeated downloads)
print("🔄 Loading embedding model...")
try:
    _get_emb()
    print("✅ Embedding model ready")
except Exception as e:
    print(f"❌ Embedding model failed: {e}")
    sys.exit(1)

print("\n🚀 NexusAI — Seeding FAISS Vector Store\n" + "─"*50)
seeded = 0

for path, dept, desc in DOCS:
    pkl_path = FAISS_DB / f"{dept}.pkl"
    
    # Skip if pkl already exists and is valid (non-zero size)
    if pkl_path.exists() and pkl_path.stat().st_size > 100:
        print(f"  ✅ {dept} already seeded — skipping")
        seeded += 1
        continue
    
    p = Path(path)
    if not p.exists():
        print(f"  ⚠  Resource not found: {path}")
        continue

    print(f"  📄 {p.name} → [{dept}]", end="  ", flush=True)
    try:
        r = ingest(p.read_bytes(), p.name, dept, "system@nexus.ai", desc)
        if r["success"]:
            print(f"✅ {r['chunks']} chunks")
            seeded += 1
        else:
            print(f"❌ {r['reason']}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "─"*50)
print(f"✅ Done! {seeded}/4 departments ready")

if seeded == 0:
    print("❌ No departments seeded — check resource files exist")
    sys.exit(1)
