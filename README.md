# Poster Design Application

A web application for processing PSD files with text layer removal capabilities.

## Features

- Upload and process PSD files
- Remove text layers from PSD files
- Optional OCR to detect and remove text in images
- Download processed files
- Responsive web interface

## Prerequisites

- Docker and Docker Compose
- Node.js and npm (for frontend development)
- Python 3.9+ (for backend development)

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd poster-design
   ```

2. **Backend Setup（Python 3.11，使用 uv 包管理）**
    ```bash
    # 安装 uv（一次性）
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # 或在 macOS：brew install uv

    cd back_end
    # 同步依赖到本地 .venv（依据 pyproject.toml / uv.lock）
    uv sync
    # 运行开发服务
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

3. **Frontend Setup**
   ```bash
   cd front_end
   npm install
   ```

### Running with Docker

1. **Build and start the services（后端基于 uv 镜像构建）**
    ```bash
    docker-compose up --build
    ```
   - 说明：Compose 中将后端的虚拟环境目录独立为命名卷 `backend_venv`，与代码挂载解耦，确保容器内依赖不被覆盖。

2. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Workflow

- **Backend**: The backend is a FastAPI application located in the `back_end` directory.
- **Frontend**: The frontend is a Vue.js application in the `front_end` directory.

## API Documentation

Once the backend is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Backend

Create a `.env` file in the `back_end` directory with the following variables:

```env
DEBUG=True
CORS_ORIGINS=["http://localhost:8080", "http://127.0.0.1:8080"]
UPLOAD_FOLDER=./uploads
TESSERACT_CMD=/usr/bin/tesseract
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
