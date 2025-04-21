import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import App from './App.vue'
import router from './router'

import 'element-plus/dist/index.css'
import './assets/style.css'

// 配置axios默认值
// 使用相对路径，通过Vite代理转发到实际的后端服务器
axios.defaults.baseURL = '/' // 相对路径，而不是绝对URL
axios.defaults.withCredentials = true // 如果需要携带cookie
axios.defaults.timeout = 15000 // 设置超时时间

// 添加请求拦截器
axios.interceptors.request.use(
  config => {
    // 在请求发送前可以进行一些处理
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器
axios.interceptors.response.use(
  response => {
    // 对响应数据做些处理
    return response
  },
  error => {
    console.error('响应错误:', error)
    if (error.response) {
      // 请求已发出，但服务器响应状态码不在 2xx 范围内
      console.error('错误状态:', error.response.status)
      console.error('错误数据:', error.response.data)
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      ElMessage.error('服务器无响应，请检查网络连接或联系管理员')
    } else {
      // 在设置请求时触发的错误
      ElMessage.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(ElementPlus)
app.use(router)

// 全局方法
app.config.globalProperties.$copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
    .then(() => {
      ElMessage.success('复制成功！')
    })
    .catch(err => {
      console.error('复制失败:', err)
      ElMessage.error('复制失败，请手动复制')
    })
}

// 挂载应用
app.mount('#app') 