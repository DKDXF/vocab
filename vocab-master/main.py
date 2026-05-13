"""
VocabMaster - FastAPI 应用入口
启动方式: python main.py
访问: http://localhost:8000
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import os

from database import init_tables
from routers import words, study, review, checkin, stats, roots, skills, wordreview, crawler, auth

app = FastAPI(title="VocabMaster", description="智能英语单词学习应用 - 三轮记忆法")

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
    """渲染主页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, summary="登录注册页面")
async def login_page(request: Request):
    """渲染登录注册页面"""
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
