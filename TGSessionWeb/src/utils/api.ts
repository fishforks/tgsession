import axios from 'axios';

// 判断当前环境
const isDev = import.meta.env.DEV;
const isProd = import.meta.env.PROD;

// 创建一个API基础实例
const api = axios.create({
  // 开发环境使用相对路径，生产环境使用环境变量中的API地址
  baseURL: isDev ? '' : import.meta.env.VITE_API_URL || '',
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  }
});

// 调试信息
if (isDev) {
  console.log('API运行在开发环境，使用相对路径 + Vite代理');
} else {
  console.log('API运行在生产环境，使用配置的基础URL:', import.meta.env.VITE_API_URL);
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证信息等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 可以在这里统一处理错误
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

export default api; 