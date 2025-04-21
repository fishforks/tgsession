<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'App'
});
</script>

<style>
:root {
  --primary-color: #409EFF;
  --secondary-color: #1e88e5;
  --success-color: #4caf50;
  --danger-color: #f44336;
  --warning-color: #ff9800;
  --info-color: #2196f3;
  --card-bg: #ffffff;
  --body-bg: #f5f7fa;
  --shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 全局增强Loading动画效果 */
.el-loading-spinner .circular {
  animation: app-loading-rotate 2s linear infinite !important;
}

.el-loading-spinner .path {
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  stroke-width: 2;
  stroke: var(--primary-color);
  stroke-linecap: round;
  animation: app-loading-dash 1.5s ease-in-out infinite !important;
}

@keyframes app-loading-dash {
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

@keyframes app-loading-rotate {
  100% {
    transform: rotate(360deg);
  }
}

/* 全局样式 */
body {
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
  margin: 0;
  padding: 0;
  background-color: var(--body-bg);
  color: #303133;
  min-height: 100vh;
  width: 100%;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 20px;
  padding-bottom: 20px;
  margin: 0;
  box-sizing: border-box;
  overflow-x: hidden;
}

.app-card {
  background-color: var(--card-bg);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 20px;
  margin-bottom: 20px;
  transition: all 0.3s;
  width: 100%;
  box-sizing: border-box;
}

.app-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}
</style> 