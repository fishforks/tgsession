import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import App from './App.vue'
import router from './router'

import 'element-plus/dist/index.css'
import './assets/style.css'

// API 配置统一在 utils/api.ts 中管理

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
  // 检查是否支持现代 Clipboard API (需要 HTTPS 环境)
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text)
      .then(() => {
        ElMessage.success('复制成功！')
      })
      .catch(err => {
        console.error('Clipboard API 复制失败:', err)
        // 如果 Clipboard API 失败，尝试传统方法
        fallbackCopyTextToClipboard(text)
      })
  } else {
    // 在 HTTP 环境或不支持的浏览器中使用传统方法
    console.log('Clipboard API 不可用，使用传统复制方法')
    fallbackCopyTextToClipboard(text)
  }
}

// 传统复制方法（兼容 HTTP 环境）
function fallbackCopyTextToClipboard(text: string) {
  const textArea = document.createElement('textarea')
  textArea.value = text
  
  // 避免滚动到底部
  textArea.style.top = '0'
  textArea.style.left = '0'
  textArea.style.position = 'fixed'
  textArea.style.opacity = '0'
  
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  
  try {
    const successful = document.execCommand('copy')
    if (successful) {
      ElMessage.success('复制成功！')
    } else {
      ElMessage.error('复制失败，请手动复制')
    }
  } catch (err) {
    console.error('传统复制方法失败:', err)
    ElMessage.error('复制失败，请手动复制')
  }
  
  document.body.removeChild(textArea)
}

// 挂载应用
app.mount('#app') 