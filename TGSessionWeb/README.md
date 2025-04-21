# Telegram Session 获取工具

这是一个基于Vue 3 + TypeScript + Vite构建的Web应用，用于获取Telegram的会话信息。采用现代化的开发流程和强类型保证，提供更好的开发体验和代码质量。

## 特性

- 手机号登录获取Session
- 二维码扫描登录获取Session
- V1格式会话转换为V2格式
- 响应式设计，适配移动设备
- TypeScript类型安全
- Vue3组合式API
- Vite快速构建和热重载

## 技术栈

- Vue 3 - 前端框架（使用组合式API）
- TypeScript - 类型安全的JavaScript
- Vite - 前端构建工具
- Element Plus - UI组件库
- Axios - HTTP客户端

## 开发环境设置

### 先决条件

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装

```bash
# 安装依赖
npm install
```

### 运行

```bash
# 开发模式运行
npm run dev
```

应用将在 http://localhost:3000 运行

### 构建

```bash
# 构建生产版本
npm run build
```

构建后的文件将生成在 `dist` 目录中。

### 预览生产版本

```bash
# 预览构建后的生产版本
npm run preview
```

## 项目结构

```
TGSessionWeb/
├── .vscode/           # VS Code配置
├── public/            # 静态资源
├── src/               # 源码
│   ├── assets/        # 资源文件
│   ├── components/    # 组件
│   │   ├── PhoneLoginComponent.vue   # 手机号登录组件
│   │   ├── QRLoginComponent.vue      # 二维码登录组件
│   │   ├── TgSessionApp.vue          # 主应用组件
│   │   └── V1ToV2Component.vue       # 会话转换组件
│   ├── types/         # TypeScript类型定义
│   │   └── index.ts   # 集中的类型声明
│   ├── App.vue        # 根组件
│   ├── env.d.ts       # 环境变量类型声明
│   └── main.ts        # 主入口文件
├── scripts/           # 辅助脚本
│   └── cleanup.js     # 清理旧JS文件脚本
├── .gitignore         # Git忽略配置
├── index.html         # HTML模板
├── package.json       # 项目配置
├── tsconfig.json      # TypeScript配置
├── tsconfig.node.json # Node环境TypeScript配置
└── vite.config.ts     # Vite配置
```

## API接口

该应用需要后端API提供以下接口：

- `/send_code` - 发送验证码
- `/verify_code` - 验证验证码
- `/verify_2fa` - 二步验证
- `/resend_code` - 重新发送验证码
- `/generate_qr_code` - 生成二维码
- `/check_qr_login` - 检查二维码登录状态
- `/convert_v1_to_v2` - 转换V1会话到V2格式

## 类型系统

项目使用TypeScript来提供类型安全，主要类型定义在`src/types/index.ts`中，包括：

- API请求和响应类型
- 会话信息类型
- 组件间通信的类型

## 使用说明

1. 选择登录方式（手机号、二维码或转换）
2. 按照界面提示完成登录
3. 获取并复制会话信息

## 清理旧文件

如果您是从旧版本升级，可以运行以下命令清理旧的JavaScript文件：

```bash
node scripts/cleanup.js
``` 