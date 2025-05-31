FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Remove EXPOSE as Heroku doesn't use it
# EXPOSE 5000

# Use the PORT environment variable from Heroku
CMD gunicorn --preload --workers=3 --bind 0.0.0.0:$PORT server:app