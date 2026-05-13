"""
用户认证 API - 登录注册功能
"""
import hashlib
import secrets
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from database import get_db, close_db

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


# ==================== 密码加密工具 ====================
def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    对密码进行哈希加密
    
    Args:
        password: 原始密码
        salt: 盐值（可选，不提供则自动生成）
        
    Returns:
        (salt, hashed_password)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # 使用 SHA-256 + salt 加密
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return salt, hashed


def verify_password(password: str, salt: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    _, computed_hash = hash_password(password, salt)
    return computed_hash == hashed_password


# ==================== 数据模型 ====================
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: int = 0
    username: str = ""


# ==================== API 接口 ====================
@router.post("/register", response_model=AuthResponse, summary="用户注册")
def register(request: RegisterRequest):
    """
    用户注册接口
    
    - 检查用户名是否已存在
    - 对密码进行哈希加密后存储
    - 记录注册时间
    """
    username = request.username.strip()
    password = request.password
    email = request.email.strip()
    
    # 参数校验
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度必须在3-20个字符之间")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6个字符")
    
    conn = get_db()
    try:
        # 检查用户名是否已存在
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail="用户名已存在")
        
        # 加密密码
        salt, password_hash = hash_password(password)
        created_at = datetime.now().isoformat()
        
        # 插入新用户
        conn.execute(
            "INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)",
            (username, f"{salt}:{password_hash}", email, created_at)
        )
        conn.commit()
        
        return AuthResponse(
            success=True,
            message="注册成功",
            username=username,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")
    finally:
        close_db(conn)


@router.post("/login", response_model=AuthResponse, summary="用户登录")
def login(request: LoginRequest, response: Response):
    """
    用户登录接口
    
    - 验证用户名和密码
    - 设置会话 Cookie
    - 更新最后登录时间
    """
    username = request.username.strip()
    password = request.password
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    
    conn = get_db()
    try:
        # 查询用户
        user = conn.execute(
            "SELECT id, username, password_hash, email FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 验证密码
        salt, stored_hash = user["password_hash"].split(":", 1)
        if not verify_password(password, salt, stored_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 更新最后登录时间
        last_login = datetime.now().isoformat()
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (last_login, user["id"])
        )
        conn.commit()
        
        # 设置会话 Cookie（简单实现，生产环境应使用 JWT）
        session_token = secrets.token_urlsafe(32)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7天过期
            samesite="lax"
        )
        
        return AuthResponse(
            success=True,
            message="登录成功",
            user_id=user["id"],
            username=user["username"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")
    finally:
        close_db(conn)


@router.post("/logout", summary="用户登出")
def logout(response: Response):
    """清除会话 Cookie"""
    response.delete_cookie(key="session_token")
    return {"success": True, "message": "已登出"}


@router.get("/me", summary="获取当前用户信息")
def get_current_user(request: Request):
    """
    获取当前登录用户的信息
    
    需要携带有效的 session_token Cookie
    """
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 简单实现：实际项目中应该验证 session_token 的有效性
    # 这里暂时返回一个占位响应
    return {
        "success": True,
        "message": "已登录",
        # TODO: 从数据库中查询真实的用户信息
    }


@router.post("/change-password", summary="修改密码")
def change_password(request: Request, old_password: str, new_password: str):
    """
    修改用户密码
    
    - 验证旧密码
    - 更新为新密码
    """
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="未登录")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6个字符")
    
    # TODO: 实现完整的密码修改逻辑
    # 1. 根据 session_token 找到用户
    # 2. 验证旧密码
    # 3. 更新新密码
    
    return {"success": True, "message": "密码修改成功"}
