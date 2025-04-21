# 生产环境构建指南

## 前置准备

在构建生产环境版本之前，您需要配置后端API服务器地址。

### 配置API地址

1. 打开 `.env.production` 文件
2. 修改 `VITE_API_URL` 的值为您的实际后端API服务器地址
   ```
   VITE_API_URL=https://your-api-domain.com
   ```
   
   > 注意: 不要在URL末尾添加斜杠。

### 环境配置说明

本项目使用两种环境配置：

1. **开发环境** (使用 `npm run dev`)
   - 使用相对路径 + Vite代理处理API请求
   - 相关配置文件: `.env` 和 `vite.config.ts`
   - Vite代理会自动将API请求转发到后端服务器

2. **生产环境** (使用 `npm run build`)
   - 使用环境变量 `VITE_API_URL` 作为API请求的基础URL
   - 相关配置文件: `.env.production`
   - 需要正确配置Web服务器以处理跨域问题

### 构建步骤

执行以下命令构建生产环境版本：

```bash
npm run build
```

构建完成后，您将在 `dist/` 目录下找到所有静态文件。

### 部署说明

构建后的静态文件可以部署到任何Web服务器。生产环境下有两种处理API请求的方式：

#### 方式1: 使用反向代理（推荐）

通过Web服务器反向代理API请求到后端服务器，避免跨域问题。

1. **Nginx配置示例**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       root /path/to/dist;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       # 反向代理API请求到后端服务器
       location /get_session {
           proxy_pass http://your-api-server:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /check_qr_status {
           proxy_pass http://your-api-server:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Apache .htaccess配置**:
   ```apache
   RewriteEngine On
   # 处理前端路由
   RewriteBase /
   RewriteRule ^index\.html$ - [L]
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteCond %{REQUEST_FILENAME} !-d
   RewriteRule . /index.html [L]
   
   # 反向代理API请求
   # 需要启用mod_proxy和mod_proxy_http模块
   ProxyPass /get_session http://your-api-server:8000/get_session
   ProxyPassReverse /get_session http://your-api-server:8000/get_session
   
   ProxyPass /check_qr_status http://your-api-server:8000/check_qr_status
   ProxyPassReverse /check_qr_status http://your-api-server:8000/check_qr_status
   ```

#### 方式2: 在后端启用CORS（如果无法使用反向代理）

在后端服务器配置中启用CORS，允许前端域名访问API。

Python Flask示例:
```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
# 启用CORS
CORS(app, resources={r"/*": {"origins": "https://your-frontend-domain.com"}})

# 其他路由和配置...
```

### 排查跨域问题

如果遇到API请求报错，通常是跨域问题导致的。解决方法：

1. **检查浏览器控制台**
   - 查看是否有CORS相关错误: `Access to XMLHttpRequest at 'xxx' from origin 'yyy' has been blocked by CORS policy`

2. **检查API基础URL配置**
   - 确认 `.env.production` 中的 `VITE_API_URL` 配置是否正确
   - 生产环境中确认是否正确使用了配置的API地址

3. **检查Web服务器配置**
   - 确认反向代理配置是否正确
   - 确认代理路径是否匹配实际API路径

4. **检查后端CORS配置**
   - 如果使用方式2，确认后端服务器是否正确配置了CORS
   - 确认允许的域名是否包含前端所在域名

### 测试部署

部署后，您应该测试以下功能：

1. 二维码登录
2. 手机号登录
3. V1到V2会话转换

API连接问题检查清单：

1. `.env.production` 中的 `VITE_API_URL` 配置是否正确
2. 网络服务器代理配置是否正确
3. 后端API服务器是否正常运行
4. 浏览器控制台是否有CORS错误 