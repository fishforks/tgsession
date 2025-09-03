<template>
  <div class="app-card">
    <h3>V1 转 V2 会话转换</h3>
    
    <div v-if="!converted" class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="V1 会话字符串" prop="v1Session">
          <el-input
            type="textarea"
            v-model="form.v1Session"
            :rows="6"
            placeholder="请输入您的 V1 会话字符串"
          ></el-input>
        </el-form-item>
        
        <div class="form-buttons">
          <el-button 
            type="primary" 
            @click="convertSession" 
            :loading="loading"
          >转换</el-button>
        </div>
      </el-form>
      
      <div v-if="error" class="error-message">
        <el-alert :title="error" type="error" show-icon :closable="false"></el-alert>
      </div>
    </div>
    
    <div v-else class="result-container">
      <div class="success-message">
        <el-alert
          title="转换成功！"
          type="success"
          description="已将 V1 会话转换为 V2 格式"
          show-icon
        ></el-alert>
      </div>
      
      <div class="session-container">
        <h4>V1 会话信息</h4>
        <el-input
          type="textarea"
          v-model="form.v1Session"
          :rows="3"
          readonly
        ></el-input>
        <div class="copy-button">
          <el-button type="primary" @click="copyToClipboard(form.v1Session)" size="small">
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
        <el-button type="primary" @click="resetForm">重新转换</el-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance } from 'element-plus';
import api from '@/utils/api';

import { ConvertV1ToV2Request, ConvertV1ToV2Response, SessionInfo } from '@/types';

interface FormData {
  v1Session: string;
}

export default defineComponent({
  name: 'V1ToV2Component',
  
  emits: ['session-received'],
  
  setup(props, { emit }) {
    const formRef = ref<FormInstance>();
    const form = ref<FormData>({
      v1Session: ''
    });
    
    const rules = {
      v1Session: [
        { required: true, message: '请输入 V1 会话字符串', trigger: 'blur' },
        { min: 10, message: 'V1 会话字符串长度不足', trigger: 'blur' }
      ]
    };
    
    const loading = ref(false);
    const error = ref('');
    const converted = ref(false);
    const v2Session = ref('');
    
    const convertSession = async () => {
      if (!formRef.value) return;
      
      // 表单验证
      try {
        await formRef.value.validate();
      } catch (error) {
        return;
      }
      
      loading.value = true;
      error.value = '';
      
      try {
        const requestData = {
          v1_session: form.value.v1Session,
          convert: true,
          use_qr: false
        };
        
        const response = await api.post<ConvertV1ToV2Response>('/get_session', requestData);
        
        if (response.data.success) {
          v2Session.value = response.data.v2_session || '';
          converted.value = true;
          
          // 触发事件通知父组件
          const sessionInfo: SessionInfo = {
            v1_session: form.value.v1Session,
            v2_session: v2Session.value
          };
          emit('session-received', sessionInfo);
        } else {
          error.value = response.data.message || '转换失败';
        }
      } catch (err: any) {
        if (err.response) {
          error.value = err.response.data.detail || '转换失败';
        } else {
          error.value = '网络错误，请稍后重试';
        }
      } finally {
        loading.value = false;
      }
    };
    
    const resetForm = () => {
      form.value.v1Session = '';
      v2Session.value = '';
      converted.value = false;
      error.value = '';
      
      if (formRef.value) {
        formRef.value.resetFields();
      }
    };
    
    const copyToClipboard = (text: string) => {
      // 使用全局的复制方法（兼容HTTP环境）
      const app = getCurrentInstance()
      if (app?.appContext.config.globalProperties.$copyToClipboard) {
        app.appContext.config.globalProperties.$copyToClipboard(text)
      } else {
        // 降级提示
        ElMessage({
          message: '复制功能不可用，请手动复制',
          type: 'error'
        });
      }
    };
    
    return {
      formRef,
      form,
      rules,
      loading,
      error,
      converted,
      v2Session,
      convertSession,
      resetForm,
      copyToClipboard
    };
  }
});
</script>

<style scoped>
.form-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 15px 0;
}

/* 强化Loading动画效果 */
:deep(.el-loading-spinner .circular) {
  animation: loading-rotate 2s linear infinite !important;
}

:deep(.el-loading-spinner .path) {
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  stroke-width: 2;
  stroke: var(--primary-color);
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

@keyframes loading-rotate {
  100% {
    transform: rotate(360deg);
  }
}

.form-buttons {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.error-message {
  margin-top: 20px;
}

.success-message {
  margin-bottom: 20px;
}

.session-container {
  margin: 20px 0;
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
  max-width: 600px;
  margin: 0 auto;
  padding: 15px 0;
}
</style> 