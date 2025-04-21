/// <reference types="vite/client" />

// 声明Vue单文件组件的模块
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 为挂载在全局的属性添加类型声明
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $copyToClipboard: (text: string) => void;
  }
} 