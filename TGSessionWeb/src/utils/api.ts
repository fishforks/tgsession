import axios from 'axios';

// 判断当前环境
const isDev = import.meta.env.DEV;
const isProd = import.meta.env.PROD;

// 创建一个API基础实例
const api = axios.create({
  // 在Docker集成部署中，始终使用相对路径，由Nginx代理到后端
  baseURL: '',
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  }
});

// 调试信息
console.log('API配置：使用相对路径，请求将由Nginx代理到后端');

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