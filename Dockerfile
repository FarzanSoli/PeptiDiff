# Use a slim base Python image
FROM python:3.12-slim

# Set environment variables to prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Set the working directory
WORKDIR /app

# Install git, curl, and necessary build dependencies for Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the application files
COPY Code ./Code

# Optional: Use a non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Specify the default command to run when the container starts
CMD ["python", "Code/Fetch_Dataset.py"]