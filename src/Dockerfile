# Dockerfile for Python Telegram Bot

# Use official Python image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables (adjust as needed)
ENV PYTHONUNBUFFERED=1 \
    TELEGRAM_BOT_TOKEN=your_bot_token \
    API_URL=http://rust-api:8000

# Command to run the bot
CMD ["python", "main.py"]