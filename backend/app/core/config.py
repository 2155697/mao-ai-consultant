"""系统配置管理"""
import os
from typing import Optional

class Settings:
    # API配置 (Kimi K2.6 - 推理模型，temperature必须为1)
    MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "sk-ttvmoQuD7rSXb3jolIUdkwkoI5LIi2ca33fdChWnr2Q0gmL9")
    MOONSHOT_BASE_URL: str = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    MOONSHOT_MODEL: str = os.getenv("MOONSHOT_MODEL", "kimi-k2.6")
    
    # 备用API配置（DeepSeek免费版或其他）
    BACKUP_API_KEY: Optional[str] = os.getenv("BACKUP_API_KEY")
    BACKUP_BASE_URL: Optional[str] = os.getenv("BACKUP_BASE_URL")
    BACKUP_MODEL: Optional[str] = os.getenv("BACKUP_MODEL")
    
    # 应用配置
    APP_NAME: str = "毛泽东风格AI咨询系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() == "true"  # 默认关闭mock，使用真实API
    
    # 模型参数 (kimi-k2.6 只支持 temperature=1)
    TEMPERATURE: float = 1.0
    MAX_TOKENS: int = 4096  # kimi-k2.6需要大token限制（reasoning+content）
    TOP_P: float = 0.9
    
    # 流式输出配置
    STREAM_CHUNK_SIZE: int = 10  # 每次发送的字符数
    STREAM_DELAY_MS: int = 20    # 模拟流式延迟
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]  # 生产环境需要限制
    
    # 性能配置
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 120  # 秒

settings = Settings()