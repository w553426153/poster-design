FROM ghcr.io/astral-sh/uv:python3.11-bookworm

WORKDIR /app/back_end

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy project manifests first to leverage Docker cache
COPY back_end/pyproject.toml ./
# If you also commit a lockfile, uncomment next line for reproducible builds
# COPY back_end/uv.lock ./

# Install dependencies into a local .venv (no dev deps)
RUN uv sync --no-dev

# Copy the application code
COPY back_end/ ./

# Create uploads directory (default mount target)
RUN mkdir -p /app/uploads

# Set environment variables
ENV PYTHONPATH=/app/back_end
# Ensure project venv is on PATH
ENV PATH=/app/back_end/.venv/bin:${PATH}
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["sh", "-lc", "[ -d .venv ] || uv sync --no-dev; uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
