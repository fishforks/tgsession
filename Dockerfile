## Multi-stage build: build Vue frontend, install Python backend, run Nginx + Uvicorn

# Build arguments for metadata
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 1) Build frontend
FROM node:18-alpine AS frontend-builder

# 安装构建依赖
RUN apk add --no-cache git

WORKDIR /build/TGSessionWeb

# 复制包配置文件并安装依赖（利用Docker缓存）
COPY TGSessionWeb/package*.json ./
RUN npm ci && npm cache clean --force

# 复制源代码并构建
COPY TGSessionWeb/ .
RUN npm run build

# 2) Final runtime with Python + Nginx
FROM python:3.11-slim AS runtime

# Build arguments
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    BACKEND_HOST=127.0.0.1 \
    BACKEND_PORT=8000 \
    WORKERS=2

# 镜像标签
LABEL org.opencontainers.image.title="TGSession" \
      org.opencontainers.image.description="TGSession - Telegram Session Manager with Web Interface" \
      org.opencontainers.image.created="${BUILDTIME}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.source="https://github.com/fish2018/tgsession"

# 安装系统依赖
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    ca-certificates \
    tzdata \
    tini \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get clean

WORKDIR /app

# 安装Python依赖（利用Docker缓存）
COPY TGSession/requirements.txt /app/TGSession/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/TGSession/requirements.txt

# 复制后端代码
COPY TGSession/ /app/TGSession/

# 复制前端构建产物
COPY --from=frontend-builder /build/TGSessionWeb/dist /app/frontend/dist

# 复制启动脚本
COPY start.sh /app/start.sh

# 设置权限和目录
RUN chmod +x /app/start.sh \
 && mkdir -p /app/logs /app/data /var/log/nginx \
 && rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf || true

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# 使用tini作为init进程
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]


