FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Fix line endings (CRLF to LF) for entrypoint script
RUN sed -i 's/\r$//' /app/compose/dev/django-entrypoint.sh

# Make entrypoint script executable
RUN chmod +x /app/compose/dev/django-entrypoint.sh


