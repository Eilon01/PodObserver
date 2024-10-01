# Use python image for amd64 as builder
FROM --platform=linux/amd64 python:3.12.5-slim AS builder

# Set environment variables to prevent writing .pyc files and unbuffer output for more reliable logging
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1

# Set the working dir
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use python image for amd64
FROM --platform=linux/amd64 python:3.12.5-slim

# Set environment variables to prevent writing .pyc files and unbuffer output for more reliable logging
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1 \
    FLASK_APP=pod-observer.py

# create new user
RUN addgroup --system python && \
    adduser --system --ingroup python python && \
    mkdir /app && \
    chown -R python:python /app

# Set the working dir
WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy app files to container
COPY pod-observer.py .
COPY templates/ .

# Switch to new user
USER python

# expose app port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "pod-observer:app", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-"]

