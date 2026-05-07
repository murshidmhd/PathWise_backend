FROM python:3.12-slim

# 1. Performance settings (standard for Django)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 2. ADD THESE TOOLS: Celery needs these to connect to your Database
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Install your libraries (celery & redis should be in here)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your PathWise code into the container
COPY . .

# 5. Expose the port for your Django API
EXPOSE 8000

# 6. Default command (Daphne handles both HTTP and WebSockets)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]
