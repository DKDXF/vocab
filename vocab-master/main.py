"""
VocabMaster - FastAPI 应用入口
启动方式: python main.py
访问: http://localhost:8000
"""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os

from database import init_tables
from routers import words, study, review, checkin, stats, roots, skills, wordreview, crawler, auth
from routers.auth import get_current_user

app = FastAPI(title="VocabMaster", description="智能英语单词学习应用 - 三轮记忆法")

# ==================== 认证中间件 ====================
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    """
    全局认证中间件：拦截所有 /api/ 开头的请求（除了 /api/auth/*）
    验证用户是否登录
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 排除不需要认证的路径
        excluded_paths = [
            "/api/auth/register",
            "/api/auth/login",
            "/login",  # 登录页面
        ]
        
        # 静态文件和登录页面不需要认证
        if path.startswith("/static/") or path in excluded_paths:
            response = await call_next(request)
            return response
        
        # 如果是 API 请求
        if path.startswith("/api/"):
            session_token = request.cookies.get("session_token")
            
            if not session_token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "未登录，请先登录"}
                )
            
            # 验证 session_token 是否有效
            from database import get_db, close_db
            conn = get_db()
            try:
                from datetime import datetime
                session = conn.execute(
                    "SELECT user_id, expires_at FROM sessions WHERE session_token = ?",
                    (session_token,)
                ).fetchone()
                
                if not session:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "会话已过期，请重新登录"}
                    )
                
                # 检查是否过期
                expires_at = datetime.fromisoformat(session["expires_at"])
                if datetime.now() > expires_at:
                    # 删除过期会话
                    conn.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
                    conn.commit()
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "会话已过期，请重新登录"}
                    )
            finally:
                close_db(conn)
        
        # 继续处理请求
        response = await call_next(request)
        return response

# 注册中间件
app.add_middleware(AuthMiddleware)

# ==================== 静态文件 & 模板 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ==================== 注册路由 ====================
app.include_router(words.router)
app.include_router(study.router)
app.include_router(review.router)
app.include_router(checkin.router)
app.include_router(stats.router)
app.include_router(roots.router)
app.include_router(skills.router)
app.include_router(wordreview.router)
app.include_router(crawler.router)
app.include_router(auth.router)


# ==================== 页面路由 ====================
@app.get("/", response_class=HTMLResponse, summary="主页面")
async def index(request: Request):
    """渲染主页面，需要登录"""
    # 检查是否登录
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return RedirectResponse(url="/login", status_code=302)
    
    # 验证 session_token 是否有效
    from database import get_db, close_db
    from datetime import datetime
    
    conn = get_db()
    try:
        session = conn.execute(
            "SELECT user_id, expires_at FROM sessions WHERE session_token = ?",
            (session_token,)
        ).fetchone()
        
        # 如果 session 不存在或已过期，重定向到登录页
        if not session:
            return RedirectResponse(url="/login", status_code=302)
        
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            # 删除过期会话
            conn.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            return RedirectResponse(url="/login", status_code=302)
    finally:
        close_db(conn)
    
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, summary="登录注册页面")
async def login_page(request: Request):
    """渲染登录注册页面（无需登录）"""
    return templates.TemplateResponse("auth.html", {"request": request})


# ==================== 启动事件 ====================
@app.on_event("startup")
async def startup():
    """应用启动时确保数据表已创建"""
    init_tables()
    print("✅ VocabMaster 已启动 -> http://localhost:8000")


# ==================== 直接运行 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
