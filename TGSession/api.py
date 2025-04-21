from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
import uvicorn
from pydantic import BaseModel
import asyncio
import os
import signal
import base64
import json
import jsonpickle
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import socks
import time
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import sys
import io

# API配置
app = FastAPI(title="TG Session API", description="获取Telegram的StringSession(V1和V2)")

# Telegram API配置
api_id = 6627460
api_hash = '27a53a0965e486a2bc1b1fcde473b1c4'

# 代理配置
proxy = (socks.SOCKS5, '127.0.0.1', 7897)
# proxy = None

# 请求模型
class SessionRequest(BaseModel):
    phone_number: Optional[str] = None
    code: Optional[str] = None
    password: Optional[str] = None
    use_qr: bool = False
    v1_session: Optional[str] = None  # 用于V1转V2

# 响应模型
class SessionResponse(BaseModel):
    success: bool
    message: str
    v1_session: Optional[str] = None  # 始终返回v1 session
    v2_session: Optional[str] = None  # 始终返回v2 session
    qr_code_base64: Optional[str] = None  # 二维码的base64编码
    qr_code_url: Optional[str] = None  # 原始二维码URL
    need_code: bool = False
    need_password: bool = False

# 存储正在进行的登录过程，使用IP作为键
active_clients: Dict[str, Any] = {}

# 添加标志来控制后台任务
background_task_control: Dict[str, bool] = {}

# 获取客户端IP地址
def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

# 用于QR码登录
async def qr_login(client_id: str) -> Dict[str, Any]:
    """使用二维码登录"""
    client = TelegramClient(StringSession(), api_id, api_hash, proxy=proxy, timeout=30, connection_retries=1)
    await client.connect()
    
    qr_login = await client.qr_login()
    
    # 获取二维码URL
    qr_url = qr_login.url
    # 将URL转换为base64编码
    qr_base64 = base64.b64encode(qr_url.encode()).decode('utf-8')
    
    return {
        "client": client,
        "qr_login": qr_login,
        "qr_base64": qr_base64,
        "qr_url": qr_url,  # 保存原始URL
        "created_at": datetime.now()  # 添加创建时间用于过期检查
    }

# V1转V2
async def convert_v1_to_v2(v1_session: str) -> str:
    """将V1 StringSession转换为V2 StringSession"""
    # 保存原始stdin
    original_stdin = sys.stdin
    
    # 创建一个模拟的stdin，当被读取时会立即触发错误而不是阻塞
    class NonInteractiveStdin:
        def readline(self):
            raise Exception("禁止交互式输入")
    
    try:
        # 临时替换标准输入
        sys.stdin = NonInteractiveStdin()
        
        async with TelegramClient(StringSession(v1_session), api_id, api_hash, proxy=proxy, timeout=30, connection_retries=1) as client:
            user = await client.get_me()
            user_id = user.id
            v1 = StringSession(v1_session)
            v1_json = json.loads(jsonpickle.encode(v1))
            dc_id = v1_json.get('_dc_id')
            ipv4 = v1_json.get('_server_address')
            port = v1_json.get('_port')
            auth_key = v1_json.get('_auth_key').get('_key')

            v2_json = json.dumps({
                "py/object": "telethon._impl.session.session.Session",
                "dcs": [{
                    "py/object": "telethon._impl.session.session.DataCenter",
                    "id": dc_id,
                    "ipv4_addr": f"{ipv4}:{port}",
                    "ipv6_addr": None,
                    "auth": auth_key
                }],
                "user": {
                    "py/object": "telethon._impl.session.session.User",
                    "id": user_id,
                    "dc": dc_id,
                    "bot": False,
                    "username": None
                },
                "state": {
                }
            })
            v2 = base64.b64encode(v2_json.encode('utf-8')).decode('utf-8')
            return v2
    finally:
        # 恢复标准输入
        sys.stdin = original_stdin

# 创建新的QR登录会话
async def create_new_qr_session(client_id: str):
    """创建新的QR登录会话替代超时的会话"""
    try:
        # 创建新的客户端和QR登录
        new_client = TelegramClient(StringSession(), api_id, api_hash, proxy=proxy, timeout=30, connection_retries=1)
        await new_client.connect()
        new_qr_login = await new_client.qr_login()
        
        # 获取新的二维码URL和base64编码
        new_qr_url = new_qr_login.url
        new_qr_base64 = base64.b64encode(new_qr_url.encode()).decode('utf-8')
        
        # 返回新的会话数据
        return {
            "client": new_client,
            "qr_login": new_qr_login,
            "qr_base64": new_qr_base64,
            "qr_url": new_qr_url,
            "created_at": datetime.now()
        }
    except Exception as e:
        print(f"创建新QR会话失败: {e}")
        raise

# QR码登录轮询
async def poll_qr_login(client_id: str, background_tasks: BackgroundTasks):
    """轮询检查QR码登录状态"""
    # 设置该客户端的任务标志为运行中
    background_task_control[client_id] = True
    
    client_data = active_clients.get(client_id)
    if not client_data:
        print(f"轮询QR码登录状态: 找不到客户端 {client_id}")
        # 移除任务标志
        background_task_control.pop(client_id, None)
        return None
    
    client = client_data["client"]
    qr_login = client_data["qr_login"]
    
    try:
        # 设置超时
        print(f"开始等待QR码扫描: {client_id}")
        result = await asyncio.wait_for(qr_login.wait(), timeout=60)
        print(f"QR码扫描结果: {result} for {client_id}")
        
        # 检查任务是否被中断
        if client_id not in background_task_control or not background_task_control[client_id]:
            print(f"QR码轮询任务已被中断: {client_id}")
            if client and client.is_connected():
                await client.disconnect()
            return None
        
        if result:
            # 成功登录
            v1_session = client.session.save()
            print(f"获取到V1 session: {client_id}")
            
            # 转换为V2 session
            try:
                v2_session = await convert_v1_to_v2(v1_session)
                print(f"成功转换为V2 session: {client_id}")
            except Exception as e:
                print(f"转换V2 session失败: {client_id}, 错误: {e}")
                v2_session = None
            
            # 设置登录成功标志，供check_qr_status接口使用
            active_clients[client_id]["login_success"] = True
            active_clients[client_id]["v1_session"] = v1_session
            active_clients[client_id]["v2_session"] = v2_session
            active_clients[client_id]["success_time"] = datetime.now()
            
            print(f"QR码登录成功，已设置状态: {client_id}")
            
            # 确保active_clients仍然存在
            if client_id in active_clients:
                return {
                    "v1_session": v1_session,
                    "v2_session": v2_session
                }
            else:
                print(f"警告: 客户端ID {client_id} 在设置成功后不存在")
                return None
    except asyncio.TimeoutError:
        print(f"QR码扫描超时: {client_id}")
        
        # 检查任务是否被中断
        if client_id not in background_task_control or not background_task_control[client_id]:
            print(f"QR码轮询任务已被中断: {client_id}")
            if client and client.is_connected():
                await client.disconnect()
            return None
        
        # 超时，创建新的QR登录会话而不是尝试重新生成
        try:
            # 先清理旧会话
            if client and client.is_connected():
                await client.disconnect()
            
            # 创建新会话
            new_session = await create_new_qr_session(client_id)
            print(f"创建新的QR会话: {client_id}")
            
            # 更新active_clients中的数据
            active_clients[client_id] = new_session
            
            # 递归继续轮询
            background_tasks.add_task(poll_qr_login, client_id, background_tasks)
        except Exception as e:
            print(f"QR超时后创建新会话失败: {e}")
            # 清理会话
            if client_id in active_clients:
                del active_clients[client_id]
    except Exception as e:
        # 出错了，清理
        print(f"QR登录轮询出错: {e} for {client_id}")
        if client and client.is_connected():
            await client.disconnect()
        if client_id in active_clients:
            del active_clients[client_id]
    
    return None

# 修改清理过期会话函数，处理QR码登录成功的会话
async def cleanup_expired_sessions():
    """定期清理过期会话"""
    while True:
        try:
            now = datetime.now()
            expired_clients = []
            
            # 查找超过15分钟的会话
            for client_id, client_data in active_clients.items():
                created_at = client_data.get("created_at")
                # 登录成功的QR会话延长保留时间到5分钟
                if client_data.get("login_success"):
                    if created_at and (now - created_at) > timedelta(minutes=5):
                        expired_clients.append(client_id)
                        print(f"清理已成功的QR会话: {client_id}")
                # 普通会话15分钟过期
                elif created_at and (now - created_at) > timedelta(minutes=15):
                    expired_clients.append(client_id)
                    print(f"清理过期会话: {client_id}")
            
            # 清理过期会话
            for client_id in expired_clients:
                client_data = active_clients[client_id]
                client = client_data.get("client")
                if client and client.is_connected():
                    await client.disconnect()
                del active_clients[client_id]
            
            # 清理过期的成功缓存
            if hasattr(app, "qr_success_cache"):
                expired_cache = []
                for client_id, cache_data in app.qr_success_cache.items():
                    if (now - cache_data["timestamp"]) > timedelta(minutes=30):
                        expired_cache.append(client_id)
                        print(f"清理过期QR成功缓存: {client_id}")
                
                for client_id in expired_cache:
                    del app.qr_success_cache[client_id]
            
            # 每30秒检查一次
            await asyncio.sleep(30)
        except Exception as e:
            print(f"清理过期会话时出错: {e}")
            await asyncio.sleep(60)  # 出错时等待时间延长

# 创建一个安全的客户端初始化函数
async def safe_phone_login(phone_number):
    # 保存原始stdin
    original_stdin = sys.stdin
    
    # 创建一个模拟的stdin，当被读取时会立即触发错误而不是阻塞
    class NonInteractiveStdin:
        def readline(self):
            raise Exception("禁止交互式输入")
    
    try:
        # 临时替换标准输入
        sys.stdin = NonInteractiveStdin()
        
        # 创建客户端，设置超时以避免长时间等待
        client = TelegramClient(StringSession(), api_id, api_hash, proxy=proxy, timeout=30, connection_retries=1)
        await client.connect()
        
        # 显式调用send_code_request，不允许交互
        await client.send_code_request(phone_number)
        
        return client
    except Exception as e:
        # 捕获并记录错误
        print(f"安全手机号登录失败: {e}")
        raise
    finally:
        # 恢复标准输入
        sys.stdin = original_stdin

@app.post("/get_session", response_model=SessionResponse)
async def get_session(request: Request, session_request: SessionRequest, background_tasks: BackgroundTasks):
    """获取Telegram StringSession
    
    支持三种方式:
    1. 通过手机号和验证码登录
    2. 通过二维码登录
    3. 将V1 StringSession转换为V2 StringSession
    
    API会同时返回V1和V2两种格式的StringSession
    """
    # 获取客户端IP作为唯一标识
    client_id = get_client_ip(request)
    
    # 如果是V1转V2
    if session_request.v1_session:
        try:
            v2_session = await convert_v1_to_v2(session_request.v1_session)
            return SessionResponse(
                success=True,
                message="成功将V1 session转换为V2 session",
                v1_session=session_request.v1_session,
                v2_session=v2_session
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")
    
    # 检查请求的登录方式，并清理可能存在的其他类型会话
    if client_id in active_clients:
        old_client_data = active_clients[client_id]
        old_client = old_client_data.get("client")
        old_login_type = old_client_data.get("login_type", "unknown")
        current_login_type = "qr" if session_request.use_qr else "phone"
        
        # 如果切换了登录类型，先清理旧会话
        if old_login_type != current_login_type:
            print(f"检测到登录方式切换: {client_id}, 从 {old_login_type} 切换到 {current_login_type}")
            
            # 中断该客户端的后台任务
            background_task_control.pop(client_id, None)
            print(f"已中断客户端 {client_id} 的后台任务")
            
            if old_client and old_client.is_connected():
                await old_client.disconnect()
            del active_clients[client_id]
            
            # 清理可能存在的成功会话缓存
            if hasattr(app, "qr_success_cache") and client_id in app.qr_success_cache:
                del app.qr_success_cache[client_id]
    
    # 如果是QR码登录
    if session_request.use_qr:
        # 启动QR登录
        try:
            # 如果该IP已经有活跃的会话，先清理
            if client_id in active_clients:
                old_client = active_clients[client_id].get("client")
                if old_client and old_client.is_connected():
                    await old_client.disconnect()
            
            qr_data = await qr_login(client_id)
            active_clients[client_id] = qr_data
            active_clients[client_id]["login_type"] = "qr"  # 标记为QR登录类型
            
            # 后台开始轮询
            background_tasks.add_task(poll_qr_login, client_id, background_tasks)
            
            return SessionResponse(
                success=True,
                message="尽快扫描二维码",
                qr_code_base64=qr_data["qr_base64"],
                qr_code_url=qr_data["qr_url"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"初始化QR登录失败: {str(e)}")
    
    # 普通登录流程
    if client_id in active_clients:
        client = active_clients[client_id]["client"]
        try:
            # 保存原始stdin
            original_stdin = sys.stdin
            
            # 创建一个模拟的stdin，当被读取时会立即触发错误而不是阻塞
            class NonInteractiveStdin:
                def readline(self):
                    raise Exception("禁止交互式输入")
            
            # 如果需要验证码
            if active_clients[client_id].get("need_code"):
                if not session_request.code:
                    return SessionResponse(
                        success=False,
                        message="请提供验证码",
                        need_code=True
                    )
                
                # 临时替换标准输入，防止在验证码提交过程中产生交互式输入
                try:
                    sys.stdin = NonInteractiveStdin()
                    await client.sign_in(phone=session_request.phone_number, code=session_request.code)
                    active_clients[client_id]["code_verified"] = True
                finally:
                    # 恢复标准输入
                    sys.stdin = original_stdin
                
                # 如果需要两步验证密码
                if active_clients[client_id].get("need_password"):
                    if not session_request.password:
                        return SessionResponse(
                            success=False,
                            message="请提供两步验证密码",
                            need_password=True
                        )
                    
                    # 临时替换标准输入，防止在密码提交过程中产生交互式输入
                    try:
                        sys.stdin = NonInteractiveStdin()
                        await client.sign_in(password=session_request.password)
                    finally:
                        # 恢复标准输入
                        sys.stdin = original_stdin
            
            # 获取V1 session
            v1_session = client.session.save()
            
            # 转换为V2 session
            v2_session = await convert_v1_to_v2(v1_session)
            
            # 清理
            await client.disconnect()
            del active_clients[client_id]
            
            return SessionResponse(
                success=True,
                message="成功获取到 session",
                v1_session=v1_session,
                v2_session=v2_session
            )
        except Exception as e:
            # 处理各种异常
            error_msg = str(e)
            if "phone code invalid" in error_msg.lower():
                return SessionResponse(
                    success=False,
                    message="验证码无效，请重新输入",
                    need_code=True
                )
            elif "2fa" in error_msg.lower() or "password" in error_msg.lower():
                active_clients[client_id]["need_password"] = True
                return SessionResponse(
                    success=False,
                    message="需要两步验证密码",
                    need_password=True
                )
            elif "禁止交互式输入" in error_msg:
                # 我们自己抛出的错误，需要更友好的错误提示
                return SessionResponse(
                    success=False,
                    message="验证过程中出现问题，请重新登录",
                    need_code=False
                )
            else:
                # 清理
                await client.disconnect()
                del active_clients[client_id]
                raise HTTPException(status_code=500, detail=f"登录失败: {error_msg}")
    
    # 初始化登录
    if not session_request.phone_number:
        raise HTTPException(status_code=400, detail="需要提供手机号码")
    
    try:
        # 如果该IP已经有活跃的会话，先清理
        if client_id in active_clients:
            old_client = active_clients[client_id].get("client")
            if old_client and old_client.is_connected():
                await old_client.disconnect()
        
        # 使用安全的非交互函数
        client = await safe_phone_login(session_request.phone_number)
        
        # 保存client状态
        active_clients[client_id] = {
            "client": client,
            "need_code": True,
            "need_password": False,
            "phone_number": session_request.phone_number,
            "created_at": datetime.now(),
            "login_type": "phone",  # 标记登录类型便于调试
            "code_verified": False  # 添加验证码验证标志
        }
        
        return SessionResponse(
            success=True,
            message="验证码已发送到您的Telegram",
            need_code=True
        )
    except Exception as e:
        # 更详细的错误处理
        error_msg = str(e)
        if "禁止交互式输入" in error_msg:
            # 我们自己抛出的错误，说明代码进入了交互模式
            return SessionResponse(
                success=False,
                message="服务器处理请求时出现问题，请稍后重试",
            )
        else:
            raise HTTPException(status_code=500, detail=f"发送验证码失败: {str(e)}")

@app.get("/check_qr_status")
async def check_qr_status(request: Request):
    """检查QR码登录状态
    
    根据客户端IP查询对应的QR码登录会话，返回登录状态
    登录成功时返回V1和V2两种格式的StringSession
    """
    # 获取客户端IP作为唯一标识
    client_id = get_client_ip(request)
    
    # 尝试从成功的会话缓存中获取
    if hasattr(app, "qr_success_cache") and client_id in app.qr_success_cache:
        cache_data = app.qr_success_cache[client_id]
        # 检查缓存是否仍然有效（5分钟内）
        if (datetime.now() - cache_data["timestamp"]) < timedelta(minutes=5):
            print(f"从缓存返回QR登录成功数据: {client_id}")
            return {
                "success": True,
                "message": "二维码登录成功",
                "v1_session": cache_data["v1_session"],
                "v2_session": cache_data["v2_session"]
            }
        else:
            # 缓存过期，删除
            del app.qr_success_cache[client_id]
    
    if client_id not in active_clients:
        raise HTTPException(status_code=404, detail="未找到您的QR码登录会话")
    
    # 检查QR码登录状态
    client_data = active_clients[client_id]
    qr_login = client_data.get("qr_login")
    
    if not qr_login:
        raise HTTPException(status_code=400, detail="该会话不是QR码登录")
    
    # 如果已经登录成功
    if client_data.get("login_success"):
        v1_session = client_data.get("v1_session")
        v2_session = client_data.get("v2_session")
        
        # 缓存成功的登录数据，而不是立即清理
        # 确保app对象有qr_success_cache属性
        if not hasattr(app, "qr_success_cache"):
            app.qr_success_cache = {}
        
        # 存储成功数据和时间戳到缓存
        app.qr_success_cache[client_id] = {
            "v1_session": v1_session,
            "v2_session": v2_session,
            "timestamp": datetime.now()
        }
        
        print(f"QR登录成功，缓存会话数据: {client_id}")
        
        # 延迟清理会话，避免前端未及时获取数据
        # 不在此处删除active_clients中的会话，改为在下次检查时判断
        
        return {
            "success": True,
            "message": "二维码登录成功",
            "v1_session": v1_session,
            "v2_session": v2_session
        }
    
    # 如果QR码已过期或需要更新，返回最新的QR码
    return {
        "success": False,
        "message": "尽快扫描二维码",
        "qr_code_base64": client_data.get("qr_base64"),
        "qr_code_url": client_data.get("qr_url")
    }

@app.get("/active_sessions")
async def active_sessions():
    """查看当前活跃的会话（仅供调试）"""
    session_info = []
    for client_id, data in active_clients.items():
        created_at = data.get("created_at", datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        session_type = "QR登录" if "qr_login" in data else "手机号登录"
        session_info.append({
            "client_id": client_id,
            "type": session_type,
            "created_at": created_at,
            "login_success": data.get("login_success", False)
        })
    
    return {
        "active_count": len(active_clients),
        "sessions": session_info
    }

@app.get("/cleanup/{client_id}")
async def cleanup_session(client_id: str):
    """清理指定客户端ID的会话（仅供调试和管理）"""
    if client_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"未找到客户端ID: {client_id}")
    
    # 中断该客户端的后台任务
    background_task_control.pop(client_id, None)
    print(f"已设置客户端 {client_id} 的后台任务终止信号")
    
    client = active_clients[client_id].get("client")
    if client and client.is_connected():
        await client.disconnect()
    
    del active_clients[client_id]
    
    # 清理可能存在的成功会话缓存
    if hasattr(app, "qr_success_cache") and client_id in app.qr_success_cache:
        del app.qr_success_cache[client_id]
    
    return {"success": True, "message": f"已清理客户端: {client_id}"}

@app.get("/cleanup_all")
async def cleanup_all_sessions():
    """清理所有会话（仅供调试和管理）"""
    count = 0
    
    # 首先中断所有后台任务
    background_task_control.clear()
    print("已设置所有后台任务终止信号")
    
    # 清理所有活跃会话
    for client_id, client_data in list(active_clients.items()):
        client = client_data.get("client")
        if client and client.is_connected():
            await client.disconnect()
        del active_clients[client_id]
        count += 1
    
    # 清理可能存在的成功会话缓存
    if hasattr(app, "qr_success_cache"):
        app.qr_success_cache.clear()
    
    print(f"已清理 {count} 个会话和所有后台任务")
    return {"success": True, "message": f"已清理 {count} 个会话和所有后台任务"}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """应用启动时的事件处理"""
    asyncio.create_task(cleanup_expired_sessions())
    asyncio.create_task(monitor_phone_login_clients())
    print("TG Session API 已启动，已启动守护进程")

async def monitor_phone_login_clients():
    """专门监控手机号登录客户端"""
    while True:
        try:
            now = datetime.now()
            for client_id, client_data in list(active_clients.items()):
                # 只处理手机号登录类型
                if client_data.get("login_type") == "phone":
                    created_at = client_data.get("created_at")
                    # 如果手机号登录客户端存在超过2分钟但仍处于初始状态
                    if created_at and (now - created_at) > timedelta(minutes=2):
                        if not client_data.get("code_verified", False):
                            print(f"检测到可能卡住的手机号登录客户端: {client_id}")
                            client = client_data.get("client")
                            if client and client.is_connected():
                                await client.disconnect()
                            del active_clients[client_id]
            
            await asyncio.sleep(30)  # 每30秒检查一次
        except Exception as e:
            print(f"监控手机号登录客户端出错: {e}")
            await asyncio.sleep(60)

# 安全输入函数替换
def safe_input(*args, **kwargs):
    print("检测到尝试进行交互式输入，程序可能卡住!")
    raise RuntimeError("请稍等几秒后重试")

# 安全替换内置输入函数
try:
    # 检查 __builtins__ 是模块还是字典
    if isinstance(__builtins__, dict):
        original_input = __builtins__["input"]
        __builtins__["input"] = safe_input
    else:
        original_input = __builtins__.input
        __builtins__.input = safe_input
    print("已成功替换input函数以防止交互式阻塞")
except Exception as e:
    print(f"替换input函数时出错: {e}")

def timeout_handler(signum, frame):
    raise TimeoutError("API请求超时")

# 在处理请求前设置超时
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30秒超时

# 请求处理完成后取消超时
signal.alarm(0)

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 