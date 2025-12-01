#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo ">>> Poster Design 部署脚本"

# 选择 compose 命令
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
else
  echo "ERROR: Docker Compose 未安装，请先安装 Docker / docker-compose。"
  exit 1
fi

echo "使用命令: $COMPOSE_CMD"

echo ">>> 1) 停止并清理旧容器..."
$COMPOSE_CMD down --remove-orphans || true

echo ">>> 2) 强制重建后端镜像..."
$COMPOSE_CMD build --no-cache backend

echo ">>> 3) 强制重建前端镜像..."
$COMPOSE_CMD build --no-cache frontend

echo ">>> 4) 重新启动服务..."
$COMPOSE_CMD up -d --force-recreate

echo ">>> 5) 当前容器状态:"
$COMPOSE_CMD ps

echo ">>> 部署完成。"
echo "Backend:  http://<your-server-ip>:8000"
echo "Frontend: http://<your-server-ip>:8081"
