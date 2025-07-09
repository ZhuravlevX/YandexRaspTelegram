# Dockerfile for Python Telegram Bot

# Use official Python image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies and locales
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    locales locales-all \
    && sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY main.py config.json5 .
COPY . ./src
RUN rm ./src/main.py ./src/config.json5

# Command to run the bot
CMD ["python", "main.py"]