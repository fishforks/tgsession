// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
}

// 会话相关类型
export interface SessionInfo {
  v1_session: string;
  v2_session: string;
}

// 手机登录相关类型
export interface PhoneLoginResponse extends ApiResponse {
  phone_code_hash?: string;
  requires_2fa?: boolean;
  hint?: string;
  v1_session?: string;
  v2_session?: string;
}

export interface SendCodeRequest {
  phone: string;
}

export interface VerifyCodeRequest {
  phone: string;
  code: string;
  phone_code_hash: string;
}

export interface Verify2FARequest {
  phone: string;
  password: string;
  phone_code_hash: string;
}

// 二维码登录相关类型
export interface QRLoginResponse extends ApiResponse {
  qr_code_base64?: string;
  qr_code_url?: string;
  login_token?: string;
  status?: 'waiting' | 'scanned' | 'confirmed' | 'expired';
  v1_session?: string;
  v2_session?: string;
  need_code?: boolean;
  need_password?: boolean;
}

export interface CheckQRLoginRequest {
  login_token: string;
}

// V1到V2转换相关类型
export interface ConvertV1ToV2Request {
  v1_session: string;
}

export interface ConvertV1ToV2Response extends ApiResponse {
  v2_session?: string;
}

// 国家信息类型
export interface Country {
  name: string;
  code: string;
} 