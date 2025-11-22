# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work dir
WORKDIR /app

# Install system dependencies required to build mysqlclient and other wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libgdk-pixbuf-xlib-2.0-dev \
    libgirepository1.0-dev \
    libffi-dev \
    shared-mime-info \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip (optional but helps get prebuilt wheels when available)
RUN pip install --upgrade pip wheel setuptools

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files (optional; fail here if Django settings not configured)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000