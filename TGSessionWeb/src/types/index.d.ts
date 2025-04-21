// 全局类型声明

// 不蒜子全局变量
interface Window {
  busuanzi_value_site_pv: number;
  busuanzi_value_site_uv: number;
  busuanzi_value_page_pv: number;
  busuanzi: {
    fetch: () => void;
  };
}

// 会话信息接口
export interface SessionInfo {
  v1_session: string;
  v2_session: string;
}

// 手机号码国家代码接口
export interface Country {
  name: string;
  code: string;
} 