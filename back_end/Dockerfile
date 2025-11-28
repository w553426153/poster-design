FROM ghcr.io/astral-sh/uv:python3.11-bookworm

WORKDIR /app/back_end

# 使用阿里云镜像源加速依赖安装
RUN rm -rf /etc/apt/sources.list /etc/apt/sources.list.d/* && \
    mkdir -p /etc/apt && \
    echo 'deb http://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update -o Dir::Etc::sourcelist="sources.list" -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0" -o Acquire::Check-Valid-Until=false -o Acquire::ForceIPv4=true && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy project manifests first to leverage Docker cache
COPY back_end/pyproject.toml ./
# If you also commit a lockfile, uncomment next line for reproducible builds
# COPY back_end/uv.lock ./

# Configure uv to use Chinese mirror sources
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/

# Install dependencies into a local .venv (no dev deps)
RUN uv sync --no-dev

# Copy the application code
COPY back_end/ ./

# Create uploads directory (default mount target)
RUN mkdir -p /app/uploads

# Create directory for u2net models and copy pre-downloaded model
RUN mkdir -p /app/models/.u2net
COPY back_end/models/u2net.onnx /app/models/.u2net/

# Set environment variables
ENV PYTHONPATH=/app/back_end
# Ensure project venv is on PATH
ENV PATH=/app/back_end/.venv/bin:${PATH}
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
# Set rembg model path to use pre-downloaded model
ENV U2NET_HOME=/app/models/.u2net

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["sh", "-lc", "[ -d .venv ] || UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ UV_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/ uv sync --no-dev; uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
