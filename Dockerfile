FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY data/ ./data/
COPY setup_database.py ./setup_database.py
COPY reset_db.py ./reset_db.py

# Create data/output directory
RUN mkdir -p data/output

# Expose port
EXPOSE 8000

# Generate data and seed database on startup
CMD ["sh", "-c", "python setup_database.py && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"]
