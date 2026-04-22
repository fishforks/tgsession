# TGSession

TGSession 是一个用于获取 Telegram Session 的 Web 应用，支持 V1 和 V2 版本，提供扫码登录和手机号登录两种方式。

🌐 **在线体验**: https://tgs.252035.xyz/

## ✨ 功能特性

- 📱 支持手机号登录获取 Session
- 📷 支持二维码扫码登录
- 🔄 支持 Session V1 和 V2 格式
- 🐳 Docker 一键部署
- 🌐 现代化 Web 界面
- 🔒 安全的会话管理

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

这是最简单的部署方式，适合大多数用户：

```bash
# 1. 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/fish2018/tgsession/main/docker-compose.yml

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
open http://localhost
```

### 方式二：Docker 命令

```bash
# 拉取镜像
docker pull ghcr.io/fish2018/tgsession:latest

# 运行容器
docker run -d \
  --name tgsession \
  -p 80:80 \
  -v tgsession-data:/app/data \
  -v tgsession-logs:/app/logs \
  -e DOMAIN=localhost \
  ghcr.io/fish2018/tgsession:latest

# 查看日志
docker logs -f tgsession
```

### 方式三：从源码构建

```bash
# 1. 克隆项目
git clone https://github.com/fish2018/tgsession.git
cd tgsession

# 2. 构建镜像
docker build -t tgsession .

# 3. 运行容器
docker run -d \
  --name tgsession \
  -p 80:80 \
  -v tgsession-data:/app/data \
  -v tgsession-logs:/app/logs \
  tgsession
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DOMAIN` | `localhost` | 访问域名 |
| `BACKEND_HOST` | `127.0.0.1` | 后端服务地址 |
| `BACKEND_PORT` | `8000` | 后端服务端口 |
| `WORKERS` | `1` | FastAPI 工作进程数。当前登录状态保存在内存中，必须使用单进程 |
| `TZ` | `Asia/Shanghai` | 时区设置 |

### HTTPS 配置

如果需要启用 HTTPS，请将 SSL 证书文件放置在挂载的数据目录中：

```bash
# 创建 SSL 证书目录
mkdir -p ./ssl

# 复制证书文件（文件名必须完全一致）
cp /path/to/your/fullchain.pem ./ssl/
cp /path/to/your/privkey.pem ./ssl/

# 更新 docker-compose.yml，取消注释 SSL 挂载部分
# - ./ssl:/app/data/ssl:ro
```

### 使用自定义配置

```yaml
version: '3.8'
services:
  tgsession:
    image: ghcr.io/fish2018/tgsession:latest
    container_name: tgsession-app
    ports:
      - "80:80"
      - "443:443"
    environment:
      - DOMAIN=your-domain.com
      - WORKERS=1
      - TZ=Asia/Shanghai
    volumes:
      - tgsession-data:/app/data
      - tgsession-logs:/app/logs
      - ./ssl:/app/data/ssl:ro  # HTTPS 证书
    restart: unless-stopped

volumes:
  tgsession-data:
  tgsession-logs:
```

## 📋 开发部署

如果需要在开发环境中部署或进行二次开发：

### 后端开发

```bash
# 1. 进入后端目录
cd TGSession

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动后端服务
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

### 前端开发

```bash
# 1. 进入前端目录
cd TGSessionWeb

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

## 🔧 传统部署

如果不使用 Docker，也可以采用传统的 Nginx + Supervisor 方式部署：

### Nginx 配置
```
server {
    # 监听HTTP请求并重定向到HTTPS
    listen 80;
    server_name tgs.252035.xyz;
    return 301 https://$host$request_uri;
}

server {
    # HTTPS配置
    listen 443 ssl http2;
    server_name tgs.252035.xyz;
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/252035.xyz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/252035.xyz/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    
    # 安全相关头部
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # 访问日志和错误日志
    access_log /var/log/nginx/tgs.access.log;
    error_log /var/log/nginx/tgs.error.log;
    
    # 前端静态文件目录 - 替换为实际路径
    root /home/work/tgsession/dist;
    index index.html;
    
    # 前端静态资源缓存配置
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # API反向代理 - 会话获取
    location = /get_session {
        proxy_pass http://127.0.0.1:8000/get_session;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API请求超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s; # 二维码登录可能需要更长时间
    }
    
    # API反向代理 - 二维码状态检查
    location = /check_qr_status {
        proxy_pass http://127.0.0.1:8000/check_qr_status;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API请求超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API反向代理 - 活跃会话查询（调试用）
    location = /active_sessions {
        proxy_pass http://127.0.0.1:8000/active_sessions;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API反向代理 - 会话清理（调试用）
    location ~ ^/cleanup {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API反向代理 - 健康检查
    location = /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
    
    # 前端路由处理 - 所有其他请求返回到index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 错误页面
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

### Supervisor 配置

如果使用 Supervisor 管理后端服务：

```ini
[program:tgs]
command=/usr/bin/python3 -m uvicorn api:app --host 127.0.0.1 --port 8000
directory=/root/work/tgsession  ; 项目的文件夹路径
autostart=true                  ; 是否在 Supervisor 启动时自动启动该程序
autorestart=true                ; 程序退出后是否自动重启
startsecs=5                     ; 程序启动需要的秒数
startretries=3                  ; 启动失败后的重试次数
exitcodes=0                     ; 程序正常退出的退出码
stopwaitsecs=5                  ; 程序停止等待的秒数
stopasgroup=true                ; 是否向进程组发送停止信号
killasgroup=true                ; 是否向进程组发送杀死信号
redirect_stderr=true            ; 是否将 stderr 重定向到 stdout
stdout_logfile_maxbytes=50MB    ; 标准输出日志文件的最大字节数
stdout_logfile=/root/work/logs/session.log
environment=PYTHONUNBUFFERED=1  ; 确保Python输出不被缓冲，实时显示日志
```

## 🚨 故障排除

### 常见问题

**Q: 容器启动失败**
```bash
# 检查容器日志
docker logs tgsession

# 检查端口是否被占用
netstat -tulpn | grep :80
```

**Q: 无法访问服务**
```bash
# 检查服务状态
docker ps
curl http://localhost/health

# 检查防火墙设置
sudo ufw status
```

**Q: Session 获取失败**
- 确保网络连接正常
- 检查 Telegram 服务器连接
- 查看容器内部日志：`docker exec -it tgsession tail -f /app/logs/backend.log`

### 维护命令

```bash
# 更新到最新版本
docker-compose pull
docker-compose up -d

# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 清理日志
docker exec tgsession sh -c 'truncate -s 0 /app/logs/*.log'

# 备份数据
docker cp tgsession:/app/data ./backup/

# 恢复数据
docker cp ./backup/data tgsession:/app/
```

## 🔒 安全建议

- 建议在生产环境中使用 HTTPS
- 定期备份重要数据
- 不要在公网直接暴露管理接口
- 使用防火墙限制访问
- 定期更新镜像版本

## 📝 更新日志

- **v1.0.0**: 初始版本，支持基本的 Session 获取功能
- 支持 Docker 部署和 GitHub Actions 自动构建

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！
