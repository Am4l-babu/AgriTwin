# Dockerfile for Cloud Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy digital twin module (needed for imports)
COPY digital_twin/ /app/cloud/digital_twin/

# Ensure cloud package is importable
RUN touch /app/cloud/__init__.py

# Expose API port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main_working:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
