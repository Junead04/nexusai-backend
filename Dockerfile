FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# CPU-only torch
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Pin numpy to avoid 1.x/2.x crash
RUN pip install --no-cache-dir numpy==1.26.4

# All other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('Model pre-downloaded successfully')"

# Copy app code
COPY . .

# Remove any local pkl files — Railway will re-seed from resource txt files
RUN rm -rf faiss_db/*.pkl 2>/dev/null || true

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]