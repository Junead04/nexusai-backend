"""Seeds TF-IDF vector store from resource txt files on startup."""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app.core.vectorstore import ingest

STORE_PATH = Path("faiss_db")
STORE_PATH.mkdir(exist_ok=True)

DOCS = [
    ("resources/employee_handbook.txt",     "general",     "Company-wide employee handbook 2024"),
    ("resources/hr_confidential.txt",        "hr",          "HR policies, salary bands, attrition data"),
    ("resources/finance_q3_report.txt",      "finance",     "Q3 FY25 financial report"),
    ("resources/engineering_guidelines.txt", "engineering", "Tech stack, dev standards, incident mgmt"),
]

print("\n🚀 NexusAI — Seeding TF-IDF Store\n" + "─"*50)
seeded = 0

for path, dept, desc in DOCS:
    pkl = STORE_PATH / f"{dept}.pkl"
    if pkl.exists() and pkl.stat().st_size > 100:
        print(f"  ✅ {dept} already seeded — skipping")
        seeded += 1
        continue
    p = Path(path)
    if not p.exists():
        print(f"  ⚠  Not found: {path}")
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
        print(f"❌ {e}")

print("\n" + "─"*50)
print(f"✅ Done! {seeded}/4 departments ready")
if seeded == 0:
    sys.exit(1)
