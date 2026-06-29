"""
FastAPI主入口 - 教员AI咨询系统
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.chat import router as chat_router

app = FastAPI(
    title="教员AI咨询系统",
    description="基于毛选98万字原文的极致蒸馏版",
    version="3.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API路由
app.include_router(chat_router, prefix="/api/v1")

# 静态文件（前端构建产物）
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
