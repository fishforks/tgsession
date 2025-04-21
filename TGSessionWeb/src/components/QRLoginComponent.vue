<template>
  <div class="app-card">
    <h3>二维码登录</h3>
    
    <transition name="fade" mode="out-in">
      <div v-if="currentStep === 0" class="qr-container" key="qr-step">
        <div v-if="error" class="error-container">
          <el-alert
            :title="error"
            type="error"
            description="无法生成二维码，可能是网络问题或服务器代理配置问题导致"
            show-icon
          ></el-alert>
          <div class="retry-info" v-if="retryCount > 0">
            <p>已尝试 {{ retryCount }} 次，请检查网络连接或稍后再试</p>
          </div>
          <div class="retry-button">
            <el-button type="primary" @click="generateQRCode" :disabled="loading || retryCount >= maxRetries">
              {{ retryCount >= maxRetries ? '请稍后再试' : '重试' }}
            </el-button>
          </div>
        </div>
        
        <div v-else class="qr-code-container">
          <!-- 二维码区域 -->
          <div class="qr-code-wrapper">
            <!-- 加载状态覆盖在二维码区域上 -->
            <div v-if="loading" class="loading-container">
              <div class="loading-content">
                <el-skeleton style="width: 100%; height: 100%" animated>
                  <template #template>
                    <el-skeleton-item variant="image" style="width: 100%; height: 100%" />
                  </template>
                </el-skeleton>
                <div class="loading-overlay">
                  <p>{{ loadingMessage }}</p>
                  <el-progress type="circle" :percentage="loadingProgress" :width="60" :duration="1" />
                </div>
              </div>
            </div>
            
            <!-- 使用原生img显示生成的二维码图像 -->
            <div v-else-if="qrImageData" class="qr-code">
              <div class="qr-img-container">
                <img :src="qrImageData" alt="登录二维码" class="qr-img" @load="imageLoaded" />
              </div>
            </div>
            
            <!-- 备用：URL链接形式 -->
            <div v-else-if="qrCodeUrl && !qrImageData" class="qr-code-text">
              <el-alert
                title="请使用以下链接登录"
                type="info"
                :closable="false"
                show-icon
              ></el-alert>
              <div class="url-container">
                <div class="url-text">{{ qrCodeUrl }}</div>
                <div class="url-actions">
                  <el-button type="primary" @click="copyToClipboard(qrCodeUrl)" size="small">
                    复制链接
                  </el-button>
                  <el-button type="success" @click="openTelegramUrl(qrCodeUrl)" size="small">
                    打开Telegram
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="qr-instructions">
            <h4>使用步骤</h4>
            <ol>
              <li>打开 Telegram 手机应用</li>
              <li>点击 <strong>设置 > 设备 > 扫描二维码</strong></li>
              <li>扫描二维码</li>
            </ol>
            
            <!-- 状态信息和进度条放在使用步骤下面 -->
            <div v-if="!loading && !error && pollingStarted" class="status-message">
              <p>{{ statusMessage }}</p>
              <el-progress 
                :percentage="progress" 
                :status="progressStatus"
                :format="() => `${progress}%`"
                :stroke-width="8"
              ></el-progress>
            </div>
            
            <div class="connection-note" v-if="retryCount > 0">
              <p class="note">注意：如果多次连接失败，可能需要检查服务器网络或代理设置</p>
            </div>
          </div>
        </div>
        
        <div class="form-buttons">
          <el-button @click="resetQR" :disabled="loading">
            重新生成二维码
          </el-button>
        </div>
      </div>
      
      <div v-else-if="currentStep === 1" class="result-container" key="result-step">
        <div class="success-message">
          <el-alert
            title="登录成功！"
            type="success"
            description="已成功获取 Telegram 会话信息"
            show-icon
            :closable="false"
          ></el-alert>
          <div class="success-icon">
            <el-icon size="48" color="#67C23A"><CircleCheckFilled /></el-icon>
          </div>
        </div>
        
        <div class="session-container">
          <h4>V1 会话信息</h4>
          <el-input
            type="textarea"
            v-model="v1Session"
            :rows="3"
            readonly
          ></el-input>
          <div class="copy-button">
            <el-button type="primary" @click="copyToClipboard(v1Session)" size="small">
              复制 V1
            </el-button>
          </div>
          
          <h4>V2 会话信息</h4>
          <el-input
            type="textarea"
            v-model="v2Session"
            :rows="3"
            readonly
          ></el-input>
          <div class="copy-button">
            <el-button type="primary" @click="copyToClipboard(v2Session)" size="small">
              复制 V2
            </el-button>
          </div>
        </div>
        
        <div class="form-buttons">
          <el-button type="primary" @click="resetForm">重新登录</el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount } from 'vue';
import { ElMessage, ElNotification } from 'element-plus';
import { CircleCheckFilled } from '@element-plus/icons-vue';
import QRCode from 'qrcode';
import api from '@/utils/api';

import { QRLoginResponse, SessionInfo } from '@/types';

export default defineComponent({
  name: 'QRLoginComponent',
  
  components: {
    CircleCheckFilled
  },
  
  emits: ['session-received'],
  
  setup(props, { emit }) {
    // 状态变量
    const currentStep = ref(0);
    const loading = ref(false);
    const error = ref('');
    const qrImageData = ref('');  // 存储二维码图像数据URL
    const qrCodeUrl = ref('');    // 存储二维码URL
    const statusMessage = ref('等待扫描...');
    const loadingMessage = ref('正在生成二维码...');
    const progress = ref(0);
    const progressStatus = ref('');
    const v1Session = ref('');
    const v2Session = ref('');
    const retryCount = ref(0);
    const maxRetries = 5;
    const pollingStarted = ref(false); // 新增：标记是否已开始轮询
    const loadingProgress = ref(10); // 新增：加载进度
    
    // 轮询状态
    let pollInterval: number | null = null;
    let loadingProgressInterval: number | null = null; // 新增：用于模拟加载进度
    
    // 显示通知
    const notify = (title: string, message: string, type = 'info') => {
      ElNotification({
        title,
        message,
        type,
        duration: 4500,
      });
    };
    
    // 生成二维码
    const generateQRCode = async () => {
      loading.value = true;
      error.value = '';
      statusMessage.value = '正在生成二维码...';
      loadingMessage.value = retryCount.value > 0 
        ? `正在尝试第 ${retryCount.value + 1} 次连接...`
        : '正在生成二维码...';
      progress.value = 0;
      progressStatus.value = '';
      pollingStarted.value = false; // 重置轮询状态标志
      qrImageData.value = '';
      qrCodeUrl.value = '';
      
      // 启动加载进度动画
      loadingProgress.value = 10; // 从10%开始
      if (loadingProgressInterval) {
        clearInterval(loadingProgressInterval);
      }
      
      // 创建更自然的进度增长效果
      const targetProgress = 90; // 最高到90%
      const duration = 6000; // 6秒内达到目标进度
      const stepTime = 200; // 每200ms更新一次
      const steps = duration / stepTime;
      const baseIncrement = (targetProgress - loadingProgress.value) / steps;
      let currentStep = 0;
      
      loadingProgressInterval = window.setInterval(() => {
        currentStep++;
        if (currentStep <= steps && loadingProgress.value < targetProgress) {
          // 添加一些随机性，让进度看起来更自然
          const randomFactor = Math.random() * 0.5 + 0.75; // 0.75-1.25之间的随机数
          const increment = baseIncrement * randomFactor;
          loadingProgress.value = Math.min(targetProgress, Math.round(loadingProgress.value + increment));
        } else if (currentStep > steps && loadingProgressInterval) {
          // 如果超过预定时间还没加载完，保持在90%
          clearInterval(loadingProgressInterval);
        }
      }, stepTime);
      
      try {
        const requestData = {
          use_qr: true
        };
        
        const response = await api.post<QRLoginResponse>('/get_session', requestData);
        console.log('二维码API响应:', response.data);
        
        if (response.data.success) {
          // 重置重试计数器
          retryCount.value = 0;
          
          // 处理二维码URL
          if (response.data.qr_code_url) {
            qrCodeUrl.value = response.data.qr_code_url;
            console.log('获取到二维码URL:', qrCodeUrl.value);
            
            // 根据URL生成二维码图像
            try {
              const qrDataUrl = await QRCode.toDataURL(qrCodeUrl.value, {
                width: 256,
                margin: 0,
                color: {
                  dark: '#000000',
                  light: '#ffffff'
                },
                errorCorrectionLevel: 'H'
              });
              
              qrImageData.value = qrDataUrl;
              console.log('二维码图像生成成功');
            } catch (err) {
              console.error('生成二维码图像失败:', err);
              // 虽然图像生成失败，但我们还有URL作为备用
            }
          } else if (response.data.qr_code_base64) {
            // 尝试解码base64为URL
            try {
              const decodedUrl = atob(response.data.qr_code_base64);
              qrCodeUrl.value = decodedUrl;
              console.log('解码base64为URL:', decodedUrl);
              
              // 根据解码后的URL生成二维码图像
              try {
                const qrDataUrl = await QRCode.toDataURL(decodedUrl, {
                  width: 256,
                  margin: 0,
                  color: {
                    dark: '#000000',
                    light: '#ffffff'
                  },
                  errorCorrectionLevel: 'H'
                });
                
                qrImageData.value = qrDataUrl;
                console.log('二维码图像生成成功');
              } catch (err) {
                console.error('生成二维码图像失败:', err);
                // 虽然图像生成失败，但我们还有URL作为备用
              }
            } catch (e) {
              console.error('解码base64为URL失败:', e);
              error.value = '二维码格式错误';
            }
          } else {
            console.error('没有收到有效的二维码数据');
            error.value = '没有收到有效的二维码数据';
            return;
          }
          
          // 没有任何有效数据
          if (!qrCodeUrl.value) {
            console.error('没有有效的登录URL');
            error.value = '没有有效的登录URL';
            return;
          }
          
          statusMessage.value = response.data.message || '请使用 Telegram 应用扫描二维码';
          
          // 开始轮询登录状态
          startPolling();
        } else {
          error.value = response.data.message || '生成二维码失败';
          retryCount.value++;
        }
      } catch (err: any) {
        console.error('生成二维码错误:', err);
        retryCount.value++;
        
        if (err.response) {
          error.value = err.response.data.detail || '生成二维码失败';
        } else if (err.message && err.message.includes('timeout')) {
          error.value = '连接超时，请检查网络设置或代理配置';
        } else {
          error.value = '网络错误，请稍后重试';
        }
        
        if (retryCount.value >= maxRetries) {
          notify(
            '连接失败', 
            `多次尝试连接Telegram服务器失败，请检查网络连接或联系管理员。`, 
            'error'
          );
        }
      } finally {
        loading.value = false;
        
        // 清除加载进度动画
        if (loadingProgressInterval) {
          clearInterval(loadingProgressInterval);
          loadingProgressInterval = null;
        }
        
        // 加载完成，确保进度显示100%
        loadingProgress.value = 100;
      }
    };
    
    // 开始轮询登录状态
    const startPolling = () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      
      // 设置QR码有效期为120秒（2分钟），Telegram的最长有效期
      const refreshInterval = 120000; // 120秒 (2分钟)
      const checkInterval = 1000; // 1秒检查一次状态，恢复原始频率
      let lastRefreshTime = Date.now();
      let lastProgressUpdate = 0; // 上次进度更新的值
      let lastMessageContent = ''; // 记录上次消息内容，避免相同消息重复设置
      
      // 初始化进度为0
      progress.value = 0;
      
      // 首次调用check_qr_status，并设置轮询开始标志
      checkLoginStatus().then(() => {
        pollingStarted.value = true;
        console.log('开始轮询状态，显示进度条');
      });
      
      pollInterval = window.setInterval(() => {
        // 检查是否需要刷新二维码
        const now = Date.now();
        if (now - lastRefreshTime >= refreshInterval) {
          console.log('二维码已过期，正在自动刷新...');
          generateQRCode();
          lastRefreshTime = now;
          return; // 已经刷新，不需要继续检查状态
        }
        
        // 检查登录状态
        checkLoginStatus();
        
        // 计算当前二维码的剩余有效时间比例
        const timeElapsed = now - lastRefreshTime;
        const timeRatio = (timeElapsed / refreshInterval) * 100;
        const currentProgress = Math.min(Math.round(timeRatio), 99);
        
        // 更新进度条，但避免频繁更新文本
        progress.value = currentProgress;
        
        // 调整进度条警告时间点
        let newMessage = '';
        if (progress.value > 85) {
          progressStatus.value = 'warning';
          newMessage = '二维码即将过期，即将自动刷新...';
        } else if (progress.value > 50) {
          progressStatus.value = '';
          // 只显示10秒的整数倍时间，避免每秒更新
          const remainingSeconds = Math.floor((refreshInterval - timeElapsed)/1000);
          const roundedSeconds = Math.floor(remainingSeconds / 10) * 10;
          newMessage = `请尽快完成扫描，二维码有效期还剩约${roundedSeconds}秒`;
        } else {
          progressStatus.value = '';
          newMessage = '尽快扫描二维码';
        }
        
        // 只有当消息内容真正变化时才更新，避免不必要的DOM更新
        if (newMessage !== lastMessageContent) {
          statusMessage.value = newMessage;
          lastMessageContent = newMessage;
        }
      }, checkInterval);
    };
    
    // 检查登录状态
    const checkLoginStatus = async () => {
      try {
        console.log('检查二维码状态...');
        
        // 使用api实例访问后端API
        const response = await api.get<QRLoginResponse>('/check_qr_status');
        
        console.log('二维码状态检查响应:', response.data);
        
        if (response.data.success) {
          // 检查是否有会话信息
          if (response.data.v1_session || response.data.v2_session) {
            // 已确认，登录成功
            v1Session.value = response.data.v1_session || '';
            v2Session.value = response.data.v2_session || '';
            statusMessage.value = '登录成功！';
            progress.value = 100;
            progressStatus.value = 'success';
            currentStep.value = 1;
            
            // 清除轮询
            if (pollInterval) {
              clearInterval(pollInterval);
            }
            
            notify(
              '登录成功', 
              '已成功获取Telegram会话信息', 
              'success'
            );
            
            // 不自动触发事件通知父组件，避免重复显示
            // 在用户点击复制按钮时才触发
          } else if (response.data.need_password) {
            // 需要输入密码（二步验证）
            statusMessage.value = '请在手机上完成二步验证...';
            progressStatus.value = 'warning';
          } else if (response.data.need_code) {
            // 已扫描，需要输入验证码
            statusMessage.value = '请在手机上输入验证码...';
            progressStatus.value = 'warning';
          } else {
            // 还在等待
            statusMessage.value = response.data.message || '等待扫描...';
          }
        } else {
          if (response.data.message && response.data.message.includes('过期')) {
            // 二维码已过期，立即刷新
            generateQRCode();
          } else {
            statusMessage.value = response.data.message || '等待扫描...';
          }
        }
        
        return response; // 确保返回响应，以便支持Promise链
      } catch (err: any) {
        console.error('检查二维码状态出错:', err);
        // 不显示错误，但记录失败次数
        if (err.message && err.message.includes('timeout')) {
          statusMessage.value = '检查状态超时，稍后重试...';
        }
        
        return Promise.resolve(null); // 确保在失败时也返回一个已解决的Promise
      }
    };
    
    // 重置二维码
    const resetQR = () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      
      pollingStarted.value = false; // 重置轮询状态
      generateQRCode();
    };
    
    // 重置表单
    const resetForm = () => {
      currentStep.value = 0;
      v1Session.value = '';
      v2Session.value = '';
      error.value = '';
      pollingStarted.value = false; // 重置轮询状态
      
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      
      generateQRCode();
    };
    
    // 复制到剪贴板
    const copyToClipboard = (text: string) => {
      navigator.clipboard.writeText(text)
        .then(() => {
          notify(
            '复制成功', 
            '已复制到剪贴板', 
            'success'
          );
          
          // 如果是复制会话信息，触发事件通知父组件
          if (text === v1Session.value || text === v2Session.value) {
            const sessionInfo: SessionInfo = {
              v1_session: v1Session.value,
              v2_session: v2Session.value
            };
            emit('session-received', sessionInfo);
          }
        })
        .catch(() => {
          notify(
            '复制失败', 
            '请手动选择文本并复制', 
            'error'
          );
        });
    };
    
    // 直接打开Telegram URL
    const openTelegramUrl = (url: string) => {
      try {
        window.open(url, '_blank');
        notify(
          '已尝试打开Telegram', 
          '如果没有自动打开，请手动复制链接', 
          'info'
        );
      } catch (e) {
        console.error('打开URL失败:', e);
        notify(
          '打开链接失败', 
          '请手动复制链接并在Telegram中输入', 
          'error'
        );
      }
    };
    
    // 添加新的处理函数
    const imageLoaded = () => {
      console.log('二维码图片加载完成');
      // 这只是为了记录事件，不需要实际执行任何操作
    };
    
    // 生命周期钩子
    onMounted(() => {
      generateQRCode();
    });
    
    // 组件卸载前清理
    onBeforeUnmount(() => {
      // 清除轮询
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
      
      // 清除加载进度动画
      if (loadingProgressInterval) {
        clearInterval(loadingProgressInterval);
        loadingProgressInterval = null;
      }
      
      // 尝试清理后端会话
      try {
        api.get('/cleanup_all').catch(error => {
          console.error('卸载组件时清理会话失败:', error);
        });
      } catch (error) {
        console.error('卸载组件时清理会话失败:', error);
      }
    });
    
    return {
      currentStep,
      loading,
      loadingMessage,
      error,
      qrImageData,
      qrCodeUrl,
      statusMessage,
      progress,
      progressStatus,
      v1Session,
      v2Session,
      retryCount,
      maxRetries,
      pollingStarted, // 导出新增的状态变量
      loadingProgress, // 导出新增的状态变量
      generateQRCode,
      resetQR,
      resetForm,
      copyToClipboard,
      openTelegramUrl,
      imageLoaded,
    };
  }
});
</script>

<style scoped>
.qr-code-container {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 20px;
  margin: 20px 0;
  transition: all 0.3s ease-in-out;
}

/* 添加红框效果样式 */
.qr-code-wrapper {
  position: relative;
  width: 260px;
  height: 260px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0; /* 去除可能的内边距 */
  margin: 0 auto; /* 水平居中 */
  box-sizing: border-box; /* 边框不影响尺寸 */
}

.loading-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f9fafc;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  z-index: 10;
  overflow: hidden;
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.loading-content {
  position: relative;
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(249, 250, 252, 0.9);
  backdrop-filter: blur(2px);
}

.loading-overlay p {
  margin: 0 0 16px;
  color: #409EFF;
  font-size: 16px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.error-container {
  margin: 20px 0;
}

.retry-button {
  margin-top: 15px;
  text-align: center;
}

@media (max-width: 768px) {
  .qr-code-container {
    flex-direction: column;
    align-items: center;
  }
  
  .qr-code-wrapper {
    margin: 0 auto 15px auto; /* 减少底部边距 */
  }
  
  .qr-instructions {
    width: 100%;
    height: auto; /* 移动设备上取消固定高度 */
    max-height: none; /* 移除最大高度限制 */
    overflow-y: visible; /* 移除滚动条 */
    padding: 12px;
  }
  
  /* 在移动设备上重新定义状态消息间距 */
  .status-message {
    margin-top: 12px;
  }
  
  /* 调整移动设备上的连接提示 */
  .connection-note {
    margin-top: 10px;
  }
}

.qr-code {
  width: 240px; /* 稍微缩小点，确保在容器内有足够边距 */
  height: 240px; /* 保持正方形 */
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  transition: all 0.3s ease;
  animation: fadeIn 0.3s ease-in-out;
  margin: auto; /* 四个方向都居中 */
  padding: 0; /* 移除内边距 */
}

.qr-img-container {
  width: 200px; /* 缩小尺寸让整体看起来更居中 */
  height: 200px; /* 保持正方形 */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  transition: all 0.3s ease;
  margin: auto; /* 四个方向都居中 */
  padding: 0; /* 移除内边距 */
}

.qr-img-container:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.1);
}

.qr-img {
  width: 180px; /* 调整宽度 */
  height: 180px; /* 调整高度 */
  object-fit: contain;
  image-rendering: crisp-edges;
  display: block; /* 防止基线对齐问题 */
  margin: auto; /* 确保图片居中 */
}

.qr-code-text {
  width: 100%;
  height: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow-y: auto;
}

.url-container {
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.url-text {
  font-family: monospace;
  word-break: break-all;
  margin-bottom: 10px;
  font-size: 12px;
}

.url-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.qr-instructions {
  flex: 1;
  padding: 15px;
  background-color: #f9fafc;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: 260px; /* 固定高度与二维码相同 */
  max-height: 260px; /* 最大高度限制 */
  overflow-y: auto; /* 添加垂直滚动条 */
  box-sizing: border-box;
}

/* 调整说明内容，确保有足够空间显示状态信息 */
.qr-instructions h4 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #333;
}

.qr-instructions ol {
  padding-left: 20px;
  margin-bottom: 10px; /* 减小底部间距 */
}

.qr-instructions li {
  margin-bottom: 5px; /* 减小列表项间距 */
  font-size: 14px; /* 稍微减小字体大小 */
}

/* 调整状态信息布局，使其更紧凑 */
.status-message {
  margin-top: 10px; /* 固定间距而不是auto */
  padding: 10px 12px; /* 减小内边距 */
  background-color: #ecf5ff;
  border-left: 4px solid #409EFF;
  border-radius: 6px;
  box-sizing: border-box;
  transition: background-color 0.5s ease;
}

.status-message p {
  color: #409EFF;
  margin-bottom: 8px; /* 减小底部间距 */
  font-weight: 500;
  font-size: 14px;
  text-align: center;
  transition: color 0.3s ease;
}

.form-buttons {
  margin-top: 25px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.form-buttons .el-button {
  padding: 10px 24px;
  transition: all 0.3s ease;
  border-radius: 6px;
}

.form-buttons .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
}

.success-message {
  margin-bottom: 20px;
  position: relative;
}

.success-icon {
  display: flex;
  justify-content: center;
  margin: 20px 0;
  animation: bounce 1s ease;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-20px);
  }
  60% {
    transform: translateY(-10px);
  }
}

.session-container {
  margin: 20px 0;
  padding: 15px;
  background-color: #f9fafc;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.session-container h4 {
  margin-bottom: 8px;
  color: #333;
}

.copy-button {
  margin: 8px 0 15px;
  display: flex;
  justify-content: flex-end;
}

.result-container {
  padding: 10px;
}

.app-card {
  transition: all 0.3s ease-in-out;
  border-radius: 8px;
  overflow: hidden;
}

.app-card h3 {
  margin-bottom: 20px;
  color: #303133;
  text-align: center;
  font-size: 20px;
  position: relative;
}

.app-card h3::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 3px;
  background-color: #409EFF;
  border-radius: 3px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.qr-container,
.result-container {
  transition: all 0.5s ease;
}

.retry-info {
  margin: 10px 0;
  font-size: 14px;
  color: #e6a23c;
}

.connection-note {
  margin-top: 8px;
  padding: 6px;
  background-color: #f8f8f8;
  border-radius: 4px;
  width: 100%;
}

.note {
  color: #e6a23c;
  font-size: 12px;
  margin: 0;
  text-align: center;
}

/* 对el-progress组件的样式覆盖，减少不必要的动画效果 */
:deep(.el-progress-bar__inner) {
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); /* 使用更平滑的过渡效果 */
}

:deep(.el-progress-bar__outer) {
  background-color: rgba(235, 238, 245, 0.6); /* 保持背景色稳定 */
}

/* 使状态文本更稳定 */
:deep(.el-progress__text) {
  min-width: 40px; /* 保持宽度稳定 */
  font-size: 12px !important; /* 固定字体大小 */
  color: #606266;
  transition: color 0.5s ease;
}

/* 增强Loading动画效果 */
:deep(.el-progress--circle) {
  margin-bottom: 10px;
}

:deep(.el-progress--circle .el-progress-circle__track) {
  stroke: #e6e6e6;
  stroke-width: 4px;
}

:deep(.el-progress--circle .el-progress-circle__path) {
  stroke: var(--primary-color);
  stroke-width: 4px;
  stroke-linecap: round;
  animation: loading-dash 1.5s ease-in-out infinite !important;
}

@keyframes loading-dash {
  0% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 120, 150;
    stroke-dashoffset: -40;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -120;
  }
}

/* 添加其他元素的旋转动画 */
.loading-overlay .el-icon {
  animation: loading-rotate 2s linear infinite;
}

@keyframes loading-rotate {
  100% {
    transform: rotate(360deg);
  }
}
</style> 