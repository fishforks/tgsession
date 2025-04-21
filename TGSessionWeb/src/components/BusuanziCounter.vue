<template>
  <div class="busuanzi-counter">
    <span id="busuanzi_container_site_uv" style="display:none" v-if="showSiteUV" class="counter-item">
      <i class="fas fa-user-friends counter-icon"></i>
      本站访客数 <span id="busuanzi_value_site_uv" class="counter-value"></span> 人次
    </span>
    <span v-if="showSiteUV && showSitePV" class="separator">•</span>
    <span id="busuanzi_container_site_pv" style="display:none" v-if="showSitePV" class="counter-item">
      <i class="fas fa-eye counter-icon"></i>
      本站总访问量 <span id="busuanzi_value_site_pv" class="counter-value"></span> 次
    </span>
    <span v-if="(showSiteUV || showSitePV) && showPagePV" class="separator">•</span>

  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

export default defineComponent({
  name: 'BusuanziCounter',
  
  props: {
    showSiteUV: {
      type: Boolean,
      default: true
    },
    showSitePV: {
      type: Boolean,
      default: true 
    },
    showPagePV: {
      type: Boolean,
      default: false
    },
    scriptUrl: {
      type: String,
      default: '//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js'
    }
  },
  
  setup(props) {
    const scriptLoaded = ref(false);
    const loadingScript = ref(false);
    const route = useRoute();
    
    // 添加meta标签以解决Chrome 85+的Referrer Policy问题
    const addMetaReferrer = () => {
      if (!document.querySelector('meta[name="referrer"]')) {
        const meta = document.createElement('meta');
        meta.name = 'referrer';
        meta.content = 'no-referrer-when-downgrade';
        document.head.appendChild(meta);
      }
    };
    
    const loadScript = () => {
      if (scriptLoaded.value || loadingScript.value) return;
      
      loadingScript.value = true;
      
      // 先移除可能存在的旧脚本，避免重复加载
      const existingScript = document.getElementById('busuanzi-script');
      if (existingScript) {
        document.head.removeChild(existingScript);
      }
      
      const script = document.createElement('script');
      script.id = 'busuanzi-script';
      script.async = true;
      script.src = props.scriptUrl;
      script.onload = () => {
        scriptLoaded.value = true;
        loadingScript.value = false;
        console.log('不蒜子统计脚本加载成功');
      };
      script.onerror = (e) => {
        loadingScript.value = false;
        console.error('不蒜子统计脚本加载失败:', e);
        // 30秒后重试加载
        setTimeout(() => {
          loadScript();
        }, 30000);
      };
      
      document.head.appendChild(script);
    };
    
    // 页面切换时重新加载不蒜子统计
    const refresh = () => {
      if (window.busuanzi_value_site_pv) {
        delete window.busuanzi_value_site_pv;
        delete window.busuanzi_value_site_uv;
        delete window.busuanzi_value_page_pv;
      }
      
      // 确保脚本加载
      if (!scriptLoaded.value && !loadingScript.value) {
        loadScript();
      } else if (scriptLoaded.value) {
        // 如果脚本已加载，调用fetch方法刷新计数
        if (typeof window.busuanzi === 'undefined') {
          // 如果脚本加载成功但busuanzi对象不存在，重新加载脚本
          scriptLoaded.value = false;
          loadScript();
        } else {
          try {
            window.busuanzi.fetch();
          } catch (error) {
            console.error('不蒜子统计刷新失败:', error);
          }
        }
      }
    };
    
    // 监听路由变化，SPA应用中刷新统计
    watch(() => route.path, (newPath, oldPath) => {
      if (newPath !== oldPath) {
        // 延迟执行，确保DOM已更新
        setTimeout(() => {
          refresh();
        }, 100);
      }
    });
    
    // 监听hashchange事件，兼容hash路由
    const handleHashChange = () => {
      refresh();
    };
    
    onMounted(() => {
      // 添加meta标签
      addMetaReferrer();
      
      // 动态加载不蒜子脚本
      loadScript();
      
      // 监听hash变化
      if (typeof window !== 'undefined') {
        window.addEventListener('hashchange', handleHashChange);
      }
    });
    
    onBeforeUnmount(() => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('hashchange', handleHashChange);
      }
    });
    
    return {
      scriptLoaded
    };
  }
});
</script>

<style scoped>
.busuanzi-counter {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  text-align: center;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.counter-item {
  display: inline-flex;
  align-items: center;
  transition: all 0.3s ease;
}

.counter-item:hover {
  color: var(--primary-color);
}

.counter-icon {
  font-size: 14px;
  margin-right: 5px;
  color: var(--primary-color);
  opacity: 0.8;
}

.separator {
  margin: 0 2px;
  color: #dcdfe6;
  font-size: 12px;
}

.counter-value {
  color: var(--primary-color);
  font-weight: 600;
  padding: 0 3px;
  display: inline-block;
  position: relative;
}

/* 数字变化时的动画 */
@keyframes counter-pop {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.counter-value:not(:empty) {
  animation: counter-pop 0.5s ease-out;
}

@media (max-width: 480px) {
  .busuanzi-counter {
    flex-direction: column;
    gap: 5px;
  }
  
  .separator {
    display: none;
  }
}
</style> 