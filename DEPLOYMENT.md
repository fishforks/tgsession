# TGSession 部署指南

本文档提供 TGSession 的详细部署说明，包括不同场景下的部署方案。

## 🐳 Docker 部署（推荐）

### 快速开始

```bash
# 下载并启动服务
curl -O https://raw.githubusercontent.com/fish2018/tgsession/main/docker-compose.yml
docker-compose up -d

# 访问应用
curl http://localhost/health
```

### 生产环境部署

#### 1. 准备环境

```bash
# 创建项目目录
mkdir -p ~/tgsession-app/{ssl,data,logs}
cd ~/tgsession-app

# 下载配置文件
curl -O https://raw.githubusercontent.com/fish2018/tgsession/main/docker-compose.yml
```

#### 2. 配置 HTTPS（可选但推荐）

```bash
# 将 SSL 证书放入 ssl 目录
cp /path/to/your/fullchain.pem ./ssl/
cp /path/to/your/privkey.pem ./ssl/

# 修改 docker-compose.yml 启用 SSL 挂载
vim docker-compose.yml
```

在 `docker-compose.yml` 中取消注释：
```yaml
volumes:
  - ./ssl:/app/data/ssl:ro
```

#### 3. 环境配置

创建 `.env` 文件：
```bash
cat > .env << EOF
DOMAIN=your-domain.com
WORKERS=4
TZ=Asia/Shanghai
EOF
```

更新 `docker-compose.yml` 使用环境文件：
```yaml
version: '3.8'
services:
  tgsession:
    image: ghcr.io/fish2018/tgsession:latest
    env_file: .env
    # ... 其他配置
```

#### 4. 启动服务

```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
docker-compose logs -f
```

#### 5. 配置反向代理（可选）

如果使用 Nginx 作为前置代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/ssl/fullchain.pem;
    ssl_certificate_key /path/to/ssl/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 源码部署

### 系统要求

- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Python 3.9+
- Node.js 18+
- Nginx 1.18+

### 后端部署

```bash
# 1. 克隆项目
git clone https://github.com/fish2018/tgsession.git
cd tgsession

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
cd TGSession
pip install -r requirements.txt

# 4. 创建服务文件
sudo tee /etc/systemd/system/tgsession.service > /dev/null << EOF
[Unit]
Description=TGSession Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/tgsession/TGSession
Environment=PATH=/path/to/tgsession/venv/bin
ExecStart=/path/to/tgsession/venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 5. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable tgsession
sudo systemctl start tgsession
```

### 前端部署

```bash
# 1. 进入前端目录
cd TGSessionWeb

# 2. 安装依赖
npm install

# 3. 构建项目
npm run build

# 4. 配置 Nginx
sudo tee /etc/nginx/sites-available/tgsession > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/tgsession/TGSessionWeb/dist;
    index index.html;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # API 代理
    location ~ ^/(get_session|check_qr_status|active_sessions|cleanup|health)$ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # SPA 路由
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 5. 启用站点
sudo ln -s /etc/nginx/sites-available/tgsession /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🌐 云平台部署

### Docker Hub / Railway

1. Fork 项目到您的 GitHub
2. 连接 Railway 到您的 GitHub
3. 部署项目，设置环境变量
4. 配置自定义域名

### AWS ECS

```bash
# 1. 构建并推送镜像
docker build -t tgsession .
docker tag tgsession:latest your-account.dkr.ecr.region.amazonaws.com/tgsession:latest
docker push your-account.dkr.ecr.region.amazonaws.com/tgsession:latest

# 2. 创建 ECS 任务定义
# 3. 创建 ECS 服务
# 4. 配置 Application Load Balancer
```

### Google Cloud Run

```bash
# 1. 构建并推送到 Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/tgsession

# 2. 部署到 Cloud Run
gcloud run deploy --image gcr.io/PROJECT-ID/tgsession --platform managed
```

## 📊 监控和维护

### 健康检查

```bash
# 检查服务状态
curl http://localhost/health

# 检查容器状态
docker ps
docker stats tgsession

# 查看日志
docker logs -f tgsession
```

### 日志管理

```bash
# 查看所有日志
docker exec tgsession tail -f /app/logs/backend.log

# 日志轮转配置
sudo tee /etc/logrotate.d/tgsession > /dev/null << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

### 备份策略

```bash
#!/bin/bash
# backup.sh - 自动备份脚本

BACKUP_DIR="/backup/tgsession"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
docker cp tgsession:/app/data $BACKUP_DIR/data_$DATE

# 备份配置
cp docker-compose.yml $BACKUP_DIR/docker-compose_$DATE.yml

# 清理旧备份（保留7天）
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +

echo "备份完成: $BACKUP_DIR"
```

设置定时备份：
```bash
# 添加到 crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### 更新升级

```bash
# 拉取最新镜像
docker-compose pull

# 重新启动服务
docker-compose up -d

# 检查更新结果
docker-compose ps
```

## 🔒 安全配置

### 防火墙设置

```bash
# UFW 配置
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables 配置
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### SSL/TLS 配置

```bash
# 使用 Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# 配置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 访问控制

在 Nginx 中限制访问：
```nginx
# 限制 IP 访问
location /admin {
    allow 192.168.1.0/24;
    deny all;
    # ... 其他配置
}

# 限制请求频率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /get_session {
    limit_req zone=api burst=5;
    # ... 其他配置
}
```

## ❓ 常见问题

### Q: 端口冲突
```bash
# 查看端口占用
sudo lsof -i :80
sudo netstat -tulpn | grep :80

# 修改端口
# 编辑 docker-compose.yml，将 "80:80" 改为 "8080:80"
```

### Q: 权限问题
```bash
# 检查文件权限
ls -la /app/data
sudo chown -R 1000:1000 /app/data
```

### Q: 性能优化
```bash
# 增加工作进程
# 在 docker-compose.yml 中设置：
environment:
  - WORKERS=4
```

### Q: 数据迁移
```bash
# 从旧版本迁移
docker cp old_container:/app/data ./migration_data
docker cp ./migration_data new_container:/app/
```

---

**需要帮助？** 请查看 [GitHub Issues](https://github.com/fish2018/tgsession/issues) 或创建新的问题报告。
