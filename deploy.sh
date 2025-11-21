#!/usr/bin/env bash

##
## 一键构建并启动 Poster Design 项目的脚本
##
## 使用方法（在服务器上）:
##   1. 确保已安装 Docker（推荐 Docker Engine 20+，自带 docker compose v2）
##   2. 将本项目代码上传或 git clone 到服务器
##   3. 在项目根目录执行:
##        chmod +x deploy.sh
##        ./deploy.sh
##
## 默认会:
##   - 构建后端镜像 (back_end/Dockerfile)
##   - 构建前端镜像 (front_end/docker/web/Dockerfile)
##   - 通过 docker-compose.yml 以后台方式启动
##

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo ">>> Building and starting Poster Design with docker compose..."

# 如果你的环境只支持 docker-compose v1，可以将 `docker compose` 改成 `docker-compose`
if command -v docker &>/dev/null; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
else
  echo "ERROR: Docker is not installed. Please install Docker first."
  exit 1
fi

echo "Using compose command: $COMPOSE_CMD"

echo ">>> Building images..."
$COMPOSE_CMD build

echo ">>> Starting containers in detached mode..."
$COMPOSE_CMD up -d

echo ">>> Done."
echo "Backend: http://<your-server-ip>:8000"
echo "Frontend: http://<your-server-ip>:8081"
echo "访问前端地址即可正常使用（前端 /api/* 已反向代理到后端服务）。"
