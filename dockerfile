# Use Python 3.11 slim imageAdd commentMore actions
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3-dev libpq-dev gcc curl \
  && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /opt/webapp

# Install Pipenv
RUN pip3 install --no-cache-dir pipenv==2024.0.1

# Copy Pipfile and Pipfile.lock first for caching
COPY Pipfile Pipfile.lock /opt/webapp/

# Install Python dependencies
RUN pipenv install --deploy --system

# Copy entire project
COPY . /opt/webapp

# Set environment path
ENV PATH="/root/.local/bin:$PATH"

# Run migrations and collect static files
RUN python manage.py collectstatic --no-input