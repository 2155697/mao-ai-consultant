"""
教员AI咨询系统 - FastAPI主入口

启动命令：
    uvicorn main:app --reload --port 8000

环境变量配置：
    MAO_API_KEY=your-api-key        # LLM API密钥（空则启用Mock模式）
    MAO_BASE_URL=https://api.moonshot.cn/v1  # API基础URL
    MAO_MODEL=kimi-k2.6             # 模型名称
    MAO_MOCK_MODE=false             # 强制Mock模式
    MAO_RAG_TOP_K=5                 # RAG检索数量
    MAO_SIGNATURE_THRESHOLD=0.3     # 签名匹配阈值

API端点：
    POST /chat/stream   SSE流式聊天
    GET /health         健康检查
"""

import sys
from pathlib import Path

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.core.config import settings
from app.core.persona_engine import persona_engine


# ── FastAPI应用实例 ──
app = FastAPI(
    title="教员AI咨询系统",
    description="基于RAG检索 + 认知签名匹配的毛泽东AI咨询后端",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS中间件 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
app.include_router(chat_router)


# ── 生命周期事件 ──
@app.on_event("startup")
async def startup_event() -> None:
    """
    应用启动时执行

    1. 验证数据文件存在
    2. 加载所有知识库数据到内存
    3. 打印启动信息
    """
    # 验证数据文件
    missing = settings.validate_data_files()
    if missing:
        print(f"[警告] 以下数据文件缺失: {missing}")
        print("[提示] 系统将尝试继续运行，但功能可能受限")

    # 加载引擎
    try:
        persona_engine.load_all()
        stats = persona_engine.get_stats()
        print("=" * 60)
        print("  教员AI咨询系统 - 后端服务已启动")
        print("=" * 60)
        print(f"  知识库chunks: {stats['chunks_count']}")
        print(f"  倒排索引词条: {stats['inverted_index_size']}")
        print(f"  概念网络概念: {stats['concepts_count']}")
        print(f"  认知签名数量: {stats['signatures_count']}")
        print(f"  人格画像加载: {'是' if stats['persona_loaded'] else '否'}")
        print(f"  Mock模式: {'是' if settings.is_mock_mode() else '否'}")
        print(f"  LLM模型: {settings.MODEL}")
        print(f"  API地址: {settings.BASE_URL}")
        print("=" * 60)
        print(f"  API文档: http://{settings.HOST}:{settings.PORT}/docs")
        print(f"  健康检查: http://{settings.HOST}:{settings.PORT}/health")
        print("=" * 60)
    except Exception as e:
        print(f"[严重错误] 引擎加载失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """应用关闭时执行"""
    print("[信息] 教员AI咨询系统 - 服务已关闭")


# ── 静态文件服务（前端构建产物） ──
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    async def root() -> dict:
        """根路径，返回服务信息"""
        return {
            "name": "教员AI咨询系统",
            "version": "2.0.0",
            "status": "running",
            "docs": "/docs",
            "endpoints": {
                "chat_stream": "POST /chat/stream (SSE)",
                "health": "GET /health",
            },
        }


# ── 直接运行入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )
