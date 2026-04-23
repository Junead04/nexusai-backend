FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# CPU-only torch (~200MB vs 2.5GB CUDA)
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Pin numpy
RUN pip install --no-cache-dir numpy==1.26.4

# All other packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Remove local pkl files — Railway re-seeds from txt resources
RUN rm -rf faiss_db/*.pkl 2>/dev/null || true

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
