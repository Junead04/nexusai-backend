FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install CPU-only torch first (prevents 2.5GB CUDA version)
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Pin numpy before installing other packages (fixes NumPy 1.x vs 2.x crash)
RUN pip install --no-cache-dir numpy==1.26.4

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model at build time (no internet needed at runtime)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('Model downloaded OK')"

COPY . .

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
