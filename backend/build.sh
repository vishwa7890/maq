#!/bin/bash
set -e

# Update pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install system dependencies for building
apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install requirements with specific build options
pip install --no-cache-dir -r requirements.txt \
    --no-warn-script-location \
    --use-pep517 \
    --compile \
    --no-cache-dir

# Create tables if needed
python -m database.database create_tables
