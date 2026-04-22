FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install CPU-only torch (200MB instead of 2.5GB CUDA version)
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model during build (not at runtime)
# This avoids cold-start download delays and permission issues on Railway
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
