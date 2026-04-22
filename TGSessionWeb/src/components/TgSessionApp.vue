<template>
  <div class="app-container">
    <!-- 滚动字幕 -->
    <div class="marquee-container">
      <div class="marquee-content">
        <span>🔔 温馨提示：真心的tgsou仅使用V1 </span>
        <span>PG的tgsearch使用V1和V2 </span>
      </div>
    </div>
    
    <h1 class="app-title">TG Session 获取工具</h1>
    
    <!-- 选择界面 -->
    <transition name="fade" mode="out-in">
      <div v-if="!activeMethod" class="app-card">
        <h3>选择登录方式</h3>
        
        <div 
          :class="['method-card']" 
          @click="activeMethod = 'phone'"
        >
          <div class="method-icon">
            <el-icon><Iphone /></el-icon>
          </div>
          <div class="method-content">
            <div class="method-title">手机号登录</div>
            <div class="method-desc">使用手机号和验证码登录，并获取Session</div>
          </div>
        </div>
        
        <div 
          :class="['method-card']" 
          @click="activeMethod = 'qr'"
        >
          <div class="method-icon">
            <el-icon><PictureFilled /></el-icon>
          </div>
          <div class="method-content">
            <div class="method-title">二维码登录</div>
            <div class="method-desc">使用Telegram扫描二维码登录，并获取Session</div>
          </div>
        </div>
        
        <div 
          :class="['method-card']" 
          @click="activeMethod = 'convert'"
        >
          <div class="method-icon">
            <el-icon><RefreshRight /></el-icon>
          </div>
          <div class="method-content">
            <div class="method-title">Session转换</div>
            <div class="method-desc">将V1格式的Session转换为V2格式</div>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 功能界面 -->
    <transition name="fade" mode="out-in">
      <div v-if="activeMethod" class="app-card">
        <div class="method-header">
          <el-button 
            type="text" 
            icon="ArrowLeft" 
            @click="backToSelection"
          >
            返回选择
          </el-button>
          <h3>
            {{ activeMethodTitle }}
          </h3>
        </div>
        
        <component 
          :is="currentComponent" 
          v-if="activeMethod" 
          @session-received="handleSessionReceived"
        ></component>
      </div>
    </transition>
    
    <!-- 页脚信息 -->
    <div class="app-footer">
      <div class="footer-wave">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320">
          <defs>
            <linearGradient id="footer-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#f7fbff;stop-opacity:0.3" />
              <stop offset="50%" style="stop-color:#f0f8ff;stop-opacity:0.2" />
              <stop offset="100%" style="stop-color:#f7fbff;stop-opacity:0.3" />
            </linearGradient>
          </defs>
          <path fill="url(#footer-gradient)" fill-opacity="0.8" d="M0,288L48,272C96,256,192,224,288,197.3C384,171,480,149,576,165.3C672,181,768,235,864,250.7C960,267,1056,245,1152,224C1248,203,1344,181,1392,170.7L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
        </svg>
      </div>
      <div class="footer-content">
        <div class="footer-info">
          <div class="footer-links">
            <a href="https://github.com/fish2018" target="_blank" class="social-link">
              <i class="fab fa-github"></i>
              <span>fish2018</span>
            </a>
            <div class="link-divider"></div>
            <a href="https://t.me/s/tgsearchers6" target="_blank" class="social-link">
              <i class="fab fa-telegram-plane"></i>
              <span>资源宇宙</span>
            </a>
          </div>
        </div>
        <div class="stats-wrapper">
          <BusuanziCounter :showSiteUV="true" :showSitePV="true" :showPagePV="true" />
        </div>
        <div class="footer-copyright">
          <p>© 2025-2035 TG Session 获取工具</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, nextTick } from 'vue';
import { ElNotification } from 'element-plus';
import { Iphone, PictureFilled, RefreshRight, CircleCheckFilled, Document, ArrowLeft } from '@element-plus/icons-vue';
import api from '@/utils/api';

import PhoneLoginComponent from './PhoneLoginComponent.vue';
import QRLoginComponent from './QRLoginComponent.vue';
import V1ToV2Component from './V1ToV2Component.vue';
import BusuanziCounter from './BusuanziCounter.vue';

import { SessionInfo, Country } from '@/types';

export default defineComponent({
  name: 'TgSessionApp',
  
  components: {
    PhoneLoginComponent,
    QRLoginComponent,
    V1ToV2Component,
    Iphone,
    PictureFilled,
    RefreshRight,
    CircleCheckFilled,
    Document,
    ArrowLeft,
    BusuanziCounter
  },
  
  setup() {
    const activeMethod = ref(''); // 默认不选择任何登录方式
    const sessionResult = ref<SessionInfo>({
      v1_session: '',
      v2_session: ''
    });
    
    const currentComponent = computed(() => {
      switch (activeMethod.value) {
        case 'phone':
          return PhoneLoginComponent;
        case 'qr':
          return QRLoginComponent;
        case 'convert':
          return V1ToV2Component;
        default:
          return null;
      }
    });
    
    const activeMethodTitle = computed(() => {
      switch (activeMethod.value) {
        case 'phone':
          return '手机号登录';
        case 'qr':
          return '二维码登录';
        case 'convert':
          return 'Session转换';
        default:
          return '';
      }
    });
    
    // 清理后端会话
    const cleanupSession = async () => {
      try {
        await api.get('/cleanup_all');
        console.log('已清理后端会话');
      } catch (error) {
        console.error('清理会话失败', error);
      }
    };
    
    const backToSelection = async () => {
      // 清理当前会话
      if (activeMethod.value === 'qr') {
        try {
          await cleanupSession();
        } catch (error) {
          console.error('清理QR会话失败', error);
        }
      }
      
      activeMethod.value = '';
      // 如果已有生成的Session，清空它
      if (sessionResult.value.v1_session || sessionResult.value.v2_session) {
        sessionResult.value = {
          v1_session: '',
          v2_session: ''
        };
      }
    };
    
    const handleSessionReceived = (result: SessionInfo) => {
      sessionResult.value = result;
      nextTick(() => {
        // 滚动到结果区域
        const resultEl = document.querySelector('.session-result');
        if (resultEl) {
          resultEl.scrollIntoView({ behavior: 'smooth' });
        }
      });
    };
    
    const notify = (title, message, type = 'info') => {
      ElNotification({
        title,
        message,
        type,
        duration: 4500,
      });
    };
    
    const copySession = (type: 'v1' | 'v2') => {
      const text = type === 'v1' ? sessionResult.value.v1_session : sessionResult.value.v2_session;
      
      // 直接使用传统复制方法，兼容所有环境
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      textArea.style.top = '0'
      textArea.style.left = '0'
      
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          notify('复制成功', `已将${type === 'v1' ? 'V1' : 'V2'} Session复制到剪贴板`, 'success');
        } else {
          notify('复制失败', '请手动选择并复制', 'error');
        }
      } catch (err) {
        console.error('复制失败:', err)
        notify('复制失败', '请手动选择并复制', 'error');
      } finally {
        document.body.removeChild(textArea)
      }
    };
    
    const countries = ref<Country[]>([
      { name: '中国', code: '+86' },
      { name: '香港', code: '+852' },
      { name: '台湾', code: '+886' },
      { name: '印尼', code: '+62' },
      { name: '马来西亚', code: '+60' },
      { name: '新加坡', code: '+65' },
      { name: '日本', code: '+81' },
      { name: '韩国', code: '+82' },
      { name: '美国', code: '+1' },
      { name: '俄罗斯', code: '+7' },
      { name: '英国', code: '+44' },
      { name: '印度', code: '+91' }
    ]);
    
    return {
      activeMethod,
      activeMethodTitle,
      sessionResult,
      currentComponent,
      handleSessionReceived,
      copySession,
      backToSelection,
      countries
    };
  }
});
</script>

<style scoped>
.app-container {
  width: 100%;
  max-width: 580px; /* 略微减小宽度，避免溢出 */
  margin: 0 auto;
  padding: 10px;
  box-sizing: border-box;
  overflow-x: hidden;
}

.app-title {
  text-align: center;
  margin-bottom: 20px;
  color: var(--primary-color);
}

.app-card {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
  background-color: white;
  width: 100%;
  box-sizing: border-box;
}

.method-card {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

.method-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 10px 0 rgba(0, 0, 0, 0.1);
}

.method-card.active {
  border-color: var(--primary-color);
  background-color: rgba(48, 163, 230, 0.05);
}

.method-icon {
  font-size: 24px;
  margin-right: 15px;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 24px; /* 确保图标有一个最小宽度 */
}

.method-content {
  flex: 1;
  min-width: 0; /* 允许内容在必要时压缩 */
}

.method-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.method-desc {
  font-size: 14px;
  color: #606266;
}

.method-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}

.method-header h3 {
  margin: 0;
  flex-grow: 1;
  text-align: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.session-result {
  margin-top: 20px;
}

.session-box {
  margin: 10px 0;
  position: relative;
}

.session-value {
  font-family: monospace;
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px;
  word-break: break-all;
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 10px;
  position: relative;
  max-height: 80px;
  overflow-y: auto;
}

.copy-icon {
  position: absolute;
  top: 5px;
  right: 5px;
  cursor: pointer;
  font-size: 16px;
  color: var(--primary-color);
  background-color: rgba(255, 255, 255, 0.8);
  padding: 3px;
  border-radius: 4px;
  z-index: 1;
}

@media (max-width: 600px) {
  .app-container {
    width: 100%;
    padding: 10px;
    margin: 0 auto;
    max-width: 100%;
  }
  
  .method-card {
    padding: 12px;
    width: 100%;
    box-sizing: border-box;
  }
  
  .app-card {
    padding: 12px;
    box-sizing: border-box;
  }
  
  .title {
    font-size: 1.5rem;
  }
  
  .method-title {
    font-size: 15px;
  }
  
  .method-desc {
    font-size: 13px;
  }
  
  .marquee-container {
    font-size: 14px;
    padding: 8px;
    max-width: 100%;
  }
  
  .footer {
    font-size: 12px;
    margin-top: 20px;
  }
}

/* 添加页脚样式 */
.app-footer {
  position: relative;
  margin-top: 60px;
  padding: 30px 0 20px;
  text-align: center;
  font-size: 14px;
  color: #606266;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  border-top: 1px dashed rgba(230, 240, 255, 0.8);
}

.footer-wave {
  position: absolute;
  top: -80px;
  left: 0;
  width: 100%;
  height: 80px;
  transform: rotate(180deg);
  z-index: -1;
  filter: drop-shadow(0 -1px 2px rgba(64, 158, 255, 0.05));
  opacity: 0.8;
}

.footer-wave svg path {
  fill: url(#footer-gradient);
}

.footer-content {
  width: 100%;
  max-width: 580px;
  position: relative;
  z-index: 1;
}

.footer-info {
  margin-bottom: 20px;
}

.footer-links {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 5px;
}

.social-link {
  display: flex;
  align-items: center;
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(230, 240, 255, 0.5);
}

.social-link i {
  margin-right: 6px;
  font-size: 16px;
  transition: all 0.3s ease;
  color: var(--primary-color);
}

.social-link:hover {
  transform: translateY(-2px);
  text-decoration: none;
  color: var(--secondary-color);
  box-shadow: 0 3px 10px rgba(64, 158, 255, 0.15);
  background-color: rgba(255, 255, 255, 0.6);
}

.social-link:hover i {
  transform: scale(1.15);
  color: var(--secondary-color);
}

.link-divider {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background-color: rgba(220, 223, 230, 0.6);
  margin: 0 8px;
}

.stats-wrapper {
  background-color: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(3px);
  border-radius: 20px;
  padding: 10px 15px;
  margin: 15px auto;
  box-shadow: 0 1px 5px 0 rgba(0, 0, 0, 0.03);
  max-width: 90%;
  transition: all 0.3s ease;
  border: 1px solid rgba(230, 240, 255, 0.5);
}

.stats-wrapper:hover {
  box-shadow: 0 2px 8px 0 rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
  background-color: rgba(255, 255, 255, 0.4);
}

.footer-copyright {
  margin-top: 15px;
  font-size: 12px;
  color: #8c9399;
}

.footer-copyright p {
  margin: 0;
  position: relative;
  display: inline-block;
  padding: 0 15px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 5px 15px;
}

.footer-copyright p:before, 
.footer-copyright p:after {
  display: none;
}

@media (max-width: 600px) {
  .app-footer {
    margin-top: 40px;
    padding: 25px 10px 15px;
  }
  
  .footer-wave {
    top: -50px;
    height: 50px;
  }
  
  .social-link {
    padding: 6px 10px;
  }
}

/* 添加滚动字幕样式 */
.marquee-container {
  width: 100%;
  max-width: 600px;
  overflow: hidden;
  background-color: #f0f8ff;
  color: #409EFF;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border-left: 4px solid #409EFF;
  position: relative;
  box-sizing: border-box;
}

.marquee-container::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 100px;
  height: 100%;
  background: linear-gradient(to right, #f0f8ff 0%, transparent 100%);
  z-index: 1;
}

.marquee-container::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  width: 100px;
  height: 100%;
  background: linear-gradient(to left, #f0f8ff 0%, transparent 100%);
  z-index: 1;
}

.marquee-content {
  display: inline-block;
  white-space: nowrap;
  animation: marquee 25s linear infinite;
  padding-left: 100%; /* 从容器外开始 */
}

.marquee-content span {
  color: #409EFF;
  font-size: 14px;
  font-weight: 500;
  padding: 0 20px;
}

.marquee-content span a {
  color: #1e88e5;
  text-decoration: none;
  font-weight: bold;
}

.marquee-content span a:hover {
  text-decoration: underline;
}

@keyframes marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-100%);
  }
}

/* 修改波浪动画 */
@keyframes wave-animation {
  0% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-25px);
  }
  100% {
    transform: translateX(0);
  }
}

.footer-wave svg {
  animation: wave-animation 15s ease-in-out infinite;
  filter: drop-shadow(0 -2px 2px rgba(64, 158, 255, 0.08));
}
</style> 