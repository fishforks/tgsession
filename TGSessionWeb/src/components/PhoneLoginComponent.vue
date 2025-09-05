<template>
  <div class="app-card">
    <h3>手机号登录</h3>
    
    <!-- 步骤导航 -->
    <div class="steps-container">
      <el-steps :active="currentStep" finish-status="success" simple>
        <el-step title="手机号"></el-step>
        <el-step title="验证码"></el-step>
        <el-step title="二步验证" v-if="requires2FA"></el-step>
        <el-step title="完成"></el-step>
      </el-steps>
    </div>
    
    <!-- 步骤 1: 输入手机号 -->
    <div v-if="currentStep === 0" class="form-container">
      <el-form :model="phoneForm" :rules="phoneRules" ref="phoneFormRef" label-position="top">
        <el-form-item label="国家/地区" prop="countryCode">
          <el-select v-model="phoneForm.countryCode" filterable placeholder="选择国家/地区代码">
            <el-option
              v-for="country in countries"
              :key="country.code"
              :label="country.name + ' (' + country.code + ')'"
              :value="country.code">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="手机号码" prop="phoneNumber">
          <el-input 
            v-model="phoneForm.phoneNumber" 
            placeholder="请输入手机号码">
            <template #prepend>{{ phoneForm.countryCode }}</template>
          </el-input>
        </el-form-item>
        
        <div class="form-buttons">
          <el-button type="primary" @click="submitPhone" :loading="loading">
            发送验证码
          </el-button>
        </div>
      </el-form>
    </div>
    
    <!-- 步骤 2: 输入验证码 -->
    <div v-else-if="currentStep === 1" class="form-container">
      <div class="phone-display">
        <span>{{ formattedPhone }}</span>
        <el-button type="text" @click="goBack(0)">修改</el-button>
      </div>
      
      <el-form :model="codeForm" :rules="codeRules" ref="codeFormRef" label-position="top">
        <el-form-item label="验证码" prop="code">
          <el-input 
            v-model="codeForm.code" 
            placeholder="请输入验证码"
            maxlength="6"
          ></el-input>
        </el-form-item>
        
        <div class="resend-container">
          <span v-if="cooldown > 0">{{ cooldown }}秒后可重新发送</span>
          <el-button 
            v-else 
            type="text" 
            @click="resendCode"
            :loading="resendLoading"
          >
            重新发送验证码
          </el-button>
        </div>
        
        <div class="form-buttons">
          <el-button @click="goBack(0)">上一步</el-button>
          <el-button type="primary" @click="submitCode" :loading="loading">
            验证
          </el-button>
        </div>
      </el-form>
    </div>
    
    <!-- 步骤 3: 输入二步验证密码 (如果需要) -->
    <div v-else-if="currentStep === 2 && requires2FA" class="form-container">
      <div class="phone-display">
        <span>{{ formattedPhone }}</span>
        <el-button type="text" @click="goBack(0)">修改</el-button>
      </div>
      
      <el-alert
        title="需要二步验证"
        type="info"
        description="请输入您在Telegram中设置的二步验证密码"
        show-icon
        :closable="false"
        style="margin-bottom: 20px;"
      ></el-alert>
      
      <el-form :model="twoFAForm" :rules="twoFARules" ref="twoFAFormRef" label-position="top">
        <el-form-item label="二步验证密码" prop="password">
          <el-input 
            v-model="twoFAForm.password" 
            placeholder="请输入二步验证密码"
            show-password
          ></el-input>
          <div v-if="twoFAHint" class="password-hint">
            密码提示: {{ twoFAHint }}
          </div>
        </el-form-item>
        
        <div class="form-buttons">
          <el-button @click="goBack(1)">上一步</el-button>
          <el-button type="primary" @click="submitTwoFA" :loading="loading">
            验证
          </el-button>
        </div>
      </el-form>
    </div>
    
    <!-- 步骤 4: 登录成功 -->
    <div v-else-if="currentStep === (requires2FA ? 3 : 2)" class="result-container">
      <div class="success-message">
        <el-alert
          title="登录成功！"
          type="success"
          description="已成功获取 Telegram 会话信息"
          show-icon
        ></el-alert>
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
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <el-alert :title="error" type="error" show-icon :closable="false"></el-alert>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onBeforeUnmount } from 'vue';
import { ElMessage, ElNotification } from 'element-plus';
import type { FormInstance } from 'element-plus';
import api from '@/utils/api';

import { 
  Country, 
  PhoneLoginResponse, 
  SendCodeRequest, 
  VerifyCodeRequest, 
  Verify2FARequest,
  SessionInfo
} from '@/types';

interface PhoneForm {
  countryCode: string;
  phoneNumber: string;
}

interface CodeForm {
  code: string;
}

interface TwoFAForm {
  password: string;
}

export default defineComponent({
  name: 'PhoneLoginComponent',
  
  emits: ['session-received'],
  
  setup(props, { emit }) {
    // 表单引用
    const phoneFormRef = ref<FormInstance>();
    const codeFormRef = ref<FormInstance>();
    const twoFAFormRef = ref<FormInstance>();
    
    // 状态变量
    const currentStep = ref(0);
    const loading = ref(false);
    const resendLoading = ref(false);
    const error = ref('');
    const cooldown = ref(0);
    let cooldownTimer: number | null = null;
    const retryCount = ref(0);
    const maxRetries = 3;
    let requestTimeout: number | null = null;
    
    // 国家代码列表
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
    
    // 手机号表单
    const phoneForm = ref<PhoneForm>({
      countryCode: '+86',
      phoneNumber: ''
    });
    
    const phoneRules = {
      countryCode: [
        { required: true, message: '请选择国家/地区代码', trigger: 'change' }
      ],
      phoneNumber: [
        { required: true, message: '请输入手机号码', trigger: 'blur' },
        { min: 5, message: '手机号码长度不正确', trigger: 'blur' }
      ]
    };
    
    // 验证码表单
    const codeForm = ref<CodeForm>({
      code: ''
    });
    
    const codeRules = {
      code: [
        { required: true, message: '请输入验证码', trigger: 'blur' },
        { min: 5, max: 6, message: '验证码为6位数字', trigger: 'blur' }
      ]
    };
    
    // 二步验证表单
    const twoFAForm = ref<TwoFAForm>({
      password: ''
    });
    
    const twoFARules = {
      password: [
        { required: true, message: '请输入二步验证密码', trigger: 'blur' },
        { min: 1, message: '密码不能为空', trigger: 'blur' }
      ]
    };
    
    // 会话信息
    const phoneCodeHash = ref('');
    const twoFAHint = ref('');
    const requires2FA = ref(false);
    const v1Session = ref('');
    const v2Session = ref('');
    
    // 计算属性
    const formattedPhone = computed(() => {
      return phoneForm.value.countryCode + ' ' + phoneForm.value.phoneNumber;
    });
    
    // 显示通知
    const notify = (title: string, message: string, type = 'info') => {
      ElNotification({
        title,
        message,
        type,
        duration: 4500,
      });
    };
    
    // 格式化手机号 - 确保格式一致
    const formatPhoneNumber = (phone: string): string => {
      // 移除所有非数字字符
      let cleaned = phone.replace(/\D/g, '');
      
      // 确保不以0开头的国际电话号码
      if (cleaned.startsWith('0')) {
        cleaned = cleaned.substring(1);
      }
      
      return cleaned;
    };
    
    // 提交手机号
    const submitPhone = async () => {
      if (!phoneFormRef.value) return;
      
      try {
        await phoneFormRef.value.validate();
      } catch (error) {
        return;
      }
      
      loading.value = true;
      error.value = '';
      
      // 格式化手机号
      const formattedPhoneNumber = phoneForm.value.countryCode + formatPhoneNumber(phoneForm.value.phoneNumber);
      
      try {
        const requestData = {
          phone_number: formattedPhoneNumber,
          use_qr: false
        };
        
        // 设置请求超时
        const timeoutPromise = new Promise((_, reject) => {
          requestTimeout = window.setTimeout(() => {
            reject(new Error('请稍等几秒后重试'));
          }, 15000); // 15秒超时
        });
        
        const responsePromise = api.post<PhoneLoginResponse>('/get_session', requestData);
        
        // 使用Promise.race进行超时控制
        const response = await Promise.race([responsePromise, timeoutPromise]) as any;
        
        // 清除超时
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        if (response.data.success) {
          // 重置重试计数
          retryCount.value = 0;
          
          phoneCodeHash.value = response.data.phone_code_hash || '';
          currentStep.value = 1;
          startCooldown(60); // 60秒冷却时间
        } else {
          error.value = response.data.message || '发送验证码失败';
          retryCount.value++;
          
          // 如果错误消息包含特定文本，可能是后端卡住
          if (response.data.message && (
              response.data.message.includes('Please enter your phone') ||
              response.data.message.includes('waiting for response')
            )) {
            error.value = '请稍等几秒后重试';
            notify('请求异常', '请稍等几秒后重试', 'warning');
          }
        }
      } catch (err: any) {
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        retryCount.value++;
        let errorMsg = '发送验证码失败';
        
        if (err.message && err.message.includes('超时')) {
          errorMsg = '请稍等几秒后重试';
        } else if (err.response) {
          errorMsg = err.response.data.detail || '发送验证码失败';
        } else {
          errorMsg = '请稍等几秒后重试';
        }
        
        error.value = errorMsg;
        
        // 达到最大重试次数时提示用户
        if (retryCount.value >= maxRetries) {
          notify(
            '多次请求失败', 
            '请确认您的手机号码正确且能收到 Telegram 的验证码，或者稍后再试。', 
            'error'
          );
        }
      } finally {
        loading.value = false;
      }
    };
    
    // 提交验证码
    const submitCode = async () => {
      if (!codeFormRef.value) return;
      
      try {
        await codeFormRef.value.validate();
      } catch (error) {
        return;
      }
      
      loading.value = true;
      error.value = '';
      
      // 格式化手机号
      const formattedPhoneNumber = phoneForm.value.countryCode + formatPhoneNumber(phoneForm.value.phoneNumber);
      
      try {
        const requestData = {
          phone_number: formattedPhoneNumber,
          code: codeForm.value.code,
          phone_code_hash: phoneCodeHash.value,
          use_qr: false
        };
        
        // 设置请求超时
        const timeoutPromise = new Promise((_, reject) => {
          requestTimeout = window.setTimeout(() => {
            reject(new Error('请稍等几秒后重试'));
          }, 20000); // 20秒超时
        });
        
        const responsePromise = api.post<PhoneLoginResponse>('/get_session', requestData);
        
        // 使用Promise.race进行超时控制
        const response = await Promise.race([responsePromise, timeoutPromise]) as any;
        
        // 清除超时
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        if (response.data.success) {
          // 重置重试计数
          retryCount.value = 0;
          
          if (response.data.need_password || response.data.requires_2fa) {
            // 需要二步验证
            requires2FA.value = true;
            twoFAHint.value = response.data.hint || '';
            currentStep.value = 2;
          } else if (response.data.v1_session || response.data.v2_session) {
            // 直接登录成功
            v1Session.value = response.data.v1_session || '';
            v2Session.value = response.data.v2_session || '';
            currentStep.value = requires2FA.value ? 3 : 2;
            notify('登录成功', '已成功获取Telegram会话信息', 'success');
          } else {
            // 成功但没有会话信息，可能有问题
            error.value = '服务器返回成功但未提供会话信息，请重试';
          }
        } else {
          // 验证码错误
          error.value = response.data.message || '验证码验证失败';
          retryCount.value++;
        }
      } catch (err: any) {
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        retryCount.value++;
        let errorMsg = '验证码验证失败';
        
        if (err.message && err.message.includes('超时')) {
          errorMsg = '请稍等几秒后重试';
        } else if (err.response) {
          errorMsg = err.response.data.detail || '验证码验证失败';
        } else {
          errorMsg = '请稍等几秒后重试';
        }
        
        error.value = errorMsg;
        
        if (retryCount.value >= maxRetries) {
          notify(
            '验证失败', 
            '多次尝试验证失败，可能是验证码已过期或者服务器问题。请重新发送验证码或稍后重试。', 
            'error'
          );
        }
      } finally {
        loading.value = false;
      }
    };
    
    // 提交二步验证密码
    const submitTwoFA = async () => {
      if (!twoFAFormRef.value) return;
      
      try {
        await twoFAFormRef.value.validate();
      } catch (error) {
        return;
      }
      
      loading.value = true;
      error.value = '';
      
      // 格式化手机号
      const formattedPhoneNumber = phoneForm.value.countryCode + formatPhoneNumber(phoneForm.value.phoneNumber);
      
      try {
        const requestData = {
          phone_number: formattedPhoneNumber,
          password: twoFAForm.value.password,
          phone_code_hash: phoneCodeHash.value,
          use_qr: false
        };
        
        // 设置请求超时
        const timeoutPromise = new Promise((_, reject) => {
          requestTimeout = window.setTimeout(() => {
            reject(new Error('请稍等几秒后重试'));
          }, 20000); // 20秒超时
        });
        
        const responsePromise = api.post<PhoneLoginResponse>('/get_session', requestData);
        
        // 使用Promise.race进行超时控制
        const response = await Promise.race([responsePromise, timeoutPromise]) as any;
        
        // 清除超时
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        if (response.data.success) {
          v1Session.value = response.data.v1_session || '';
          v2Session.value = response.data.v2_session || '';
          currentStep.value = 3;
          notify('登录成功', '已成功获取Telegram会话信息', 'success');
        } else {
          error.value = response.data.message || '二步验证失败';
          retryCount.value++;
        }
      } catch (err: any) {
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        retryCount.value++;
        let errorMsg = '二步验证失败';
        
        if (err.message && err.message.includes('超时')) {
          errorMsg = '请稍等几秒后重试';
        } else if (err.response) {
          errorMsg = err.response.data.detail || '二步验证失败';
        } else {
          errorMsg = '请稍等几秒后重试';
        }
        
        error.value = errorMsg;
      } finally {
        loading.value = false;
      }
    };
    
    // 重新发送验证码
    const resendCode = async () => {
      resendLoading.value = true;
      error.value = '';
      
      // 格式化手机号
      const formattedPhoneNumber = phoneForm.value.countryCode + formatPhoneNumber(phoneForm.value.phoneNumber);
      
      try {
        const requestData = {
          phone_number: formattedPhoneNumber,
          resend: true
        };
        
        // 设置请求超时
        const timeoutPromise = new Promise((_, reject) => {
          requestTimeout = window.setTimeout(() => {
            reject(new Error('请稍等几秒后重试'));
          }, 15000); // 15秒超时
        });
        
        const responsePromise = api.post<PhoneLoginResponse>('/get_session', requestData);
        
        // 使用Promise.race进行超时控制
        const response = await Promise.race([responsePromise, timeoutPromise]) as any;
        
        // 清除超时
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        if (response.data.success) {
          phoneCodeHash.value = response.data.phone_code_hash || '';
          startCooldown(60); // 60秒冷却时间
          notify('验证码已发送', '新的验证码已发送到您的Telegram账号', 'success');
        } else {
          error.value = response.data.message || '重新发送验证码失败';
          retryCount.value++;
        }
      } catch (err: any) {
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          requestTimeout = null;
        }
        
        retryCount.value++;
        let errorMsg = '重新发送验证码失败';
        
        if (err.message && err.message.includes('超时')) {
          errorMsg = '请稍等几秒后重试';
        } else if (err.response) {
          errorMsg = err.response.data.detail || '重新发送验证码失败';
        } else {
          errorMsg = '请稍等几秒后重试';
        }
        
        error.value = errorMsg;
      } finally {
        resendLoading.value = false;
      }
    };
    
    // 返回上一步
    const goBack = (step: number) => {
      currentStep.value = step;
      error.value = '';
    };
    
    // 开始冷却倒计时
    const startCooldown = (seconds: number) => {
      cooldown.value = seconds;
      
      if (cooldownTimer) {
        clearInterval(cooldownTimer);
      }
      
      cooldownTimer = window.setInterval(() => {
        cooldown.value--;
        
        if (cooldown.value <= 0 && cooldownTimer) {
          clearInterval(cooldownTimer);
        }
      }, 1000);
    };
    
    // 重置表单
    const resetForm = () => {
      currentStep.value = 0;
      requires2FA.value = false;
      v1Session.value = '';
      v2Session.value = '';
      error.value = '';
      phoneCodeHash.value = '';
      twoFAHint.value = '';
      retryCount.value = 0;
      
      // 清除所有超时器
      if (requestTimeout) {
        clearTimeout(requestTimeout);
        requestTimeout = null;
      }
      
      phoneForm.value.phoneNumber = '';
      codeForm.value.code = '';
      twoFAForm.value.password = '';
      
      if (cooldownTimer) {
        clearInterval(cooldownTimer);
        cooldown.value = 0;
      }
      
      if (phoneFormRef.value) {
        phoneFormRef.value.resetFields();
      }
      
      if (codeFormRef.value) {
        codeFormRef.value.resetFields();
      }
      
      if (twoFAFormRef.value) {
        twoFAFormRef.value.resetFields();
      }
    };
    
    // 复制到剪贴板
    const copyToClipboard = (text: string) => {
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
          notify('复制成功', '已复制到剪贴板', 'success');
          
          // 如果是复制会话信息，触发事件通知父组件
          if (text === v1Session.value || text === v2Session.value) {
            const sessionInfo: SessionInfo = {
              v1_session: v1Session.value,
              v2_session: v2Session.value
            };
            emit('session-received', sessionInfo);
          }
        } else {
          notify('复制失败', '请手动选择文本并复制', 'error');
        }
      } catch (err) {
        console.error('复制失败:', err)
        notify('复制失败', '请手动选择文本并复制', 'error');
      } finally {
        document.body.removeChild(textArea)
      }
    };
    
    // 组件卸载前清理
    onBeforeUnmount(() => {
      if (cooldownTimer) {
        clearInterval(cooldownTimer);
      }
      
      if (requestTimeout) {
        clearTimeout(requestTimeout);
      }
    });
    
    return {
      phoneFormRef,
      codeFormRef,
      twoFAFormRef,
      currentStep,
      loading,
      resendLoading,
      error,
      cooldown,
      countries,
      phoneForm,
      phoneRules,
      codeForm,
      codeRules,
      twoFAForm,
      twoFARules,
      requires2FA,
      twoFAHint,
      v1Session,
      v2Session,
      formattedPhone,
      submitPhone,
      submitCode,
      submitTwoFA,
      resendCode,
      goBack,
      resetForm,
      copyToClipboard,
      retryCount,
      maxRetries
    };
  }
});
</script>

<style scoped>
.app-card {
  background-color: #ffffff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 25px;
  width: 100%;
  box-sizing: border-box;
}

.steps-container {
  margin-bottom: 20px;
}

.form-container {
  width: 100%;
}

.form-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.phone-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.resend-container {
  text-align: right;
  margin: 10px 0;
  font-size: 14px;
  color: #606266;
}

.password-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.result-container {
  width: 100%;
}

.success-message {
  margin-bottom: 20px;
}

.session-container {
  margin-top: 20px;
}

.session-container h4 {
  margin: 15px 0 5px 0;
  color: #303133;
}

.copy-button {
  text-align: right;
  margin: 5px 0 15px 0;
}

.error-message {
  margin-top: 20px;
}

/* 响应式样式调整 */
@media (max-width: 600px) {
  .app-card {
    padding: 15px;
    border-radius: 6px;
  }

  .form-buttons {
    flex-direction: column;
    gap: 10px;
  }

  .form-buttons .el-button {
    width: 100%;
    margin-left: 0 !important;
  }

  .phone-display {
    font-size: 14px;
    padding: 6px 10px;
  }

  /* 调整步骤导航的样式 */
  :deep(.el-steps--simple) {
    padding: 10px 0;
  }

  :deep(.el-step__title) {
    font-size: 12px;
  }

  /* 确保表单元素在小屏幕上完全填充 */
  :deep(.el-select),
  :deep(.el-input) {
    width: 100%;
  }

  /* 调整会话信息文本框大小 */
  .session-container textarea {
    font-size: 12px;
  }
}
</style> 