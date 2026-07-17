FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY backend/ ./backend/
COPY data/ ./data/
COPY setup_database.py ./setup_database.py

# Create data/output directory for generated CSVs
RUN mkdir -p data/output

# Default port (Render overrides via PORT env var)
ENV PORT=8000
EXPOSE $PORT

# Generate data, seed database, and start server
CMD ["sh", "-c", "python setup_database.py && cd backend && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
