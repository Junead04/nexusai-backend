FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# CPU-only torch
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Pin numpy
RUN pip install --no-cache-dir numpy==1.26.4

# All other packages
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download small embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; print('Downloading all-MiniLM-L3-v2...'); m = SentenceTransformer('all-MiniLM-L3-v2'); print('Model ready:', m.get_sentence_embedding_dimension(), 'dimensions')"

COPY . .

# Delete old pkl files
RUN rm -f faiss_db/*.pkl || true
RUN echo 'Old pkl files removed — will re-seed with L3 model on startup'

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]