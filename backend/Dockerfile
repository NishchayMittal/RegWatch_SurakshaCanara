FROM python:3.11-slim

# Install necessary system dependencies (SQLite, C++ build tools for ChromaDB/Transformers if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the backend API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
