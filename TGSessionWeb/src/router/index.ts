import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import TgSessionApp from '../components/TgSessionApp.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: TgSessionApp
  },
  // 可以根据需要添加更多路由
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 