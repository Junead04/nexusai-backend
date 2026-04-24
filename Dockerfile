FROM python:3.11-slim

WORKDIR /app

# Install all packages - no torch, no sentence-transformers, no heavy ML
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify scikit-learn works
RUN python -c "from sklearn.feature_extraction.text import TfidfVectorizer; print('TF-IDF ready')"

COPY . .

# Remove any old pkl files (incompatible with new TF-IDF store)
RUN rm -rf faiss_db/*.pkl 2>/dev/null || true

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
