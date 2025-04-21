# tgsession
https://tgs.252035.xyz/ 在线获取TG Session V1 V2，支持扫码、手机号获取

# 部署配置参考
`nginx配置`
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

如果使用supervisor部署后端，可以参考配置
```
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
