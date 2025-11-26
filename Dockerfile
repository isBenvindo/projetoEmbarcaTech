# Dockerfile
# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
# This now copies the 'app' directory from the 'back-end' folder
COPY ./back-end/app /app/app

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Give ownership of the app directory to the new user.
# This is the FIX for the PermissionError, allowing the app to write log files.
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn
# The entry point is now 'app.main:app'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]