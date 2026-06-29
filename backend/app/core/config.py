"""
配置管理模块
"""
import os
from pathlib import Path


class Settings:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"

    API_KEY: str = os.getenv("MAO_API_KEY", "")
    BASE_URL: str = os.getenv("MAO_BASE_URL", "https://api.moonshot.cn/v1")
    MODEL: str = os.getenv("MAO_MODEL", "kimi-k2.6")
    TEMPERATURE: float = float(os.getenv("MAO_TEMPERATURE", "1.0"))
    MAX_TOKENS: int = int(os.getenv("MAO_MAX_TOKENS", "4096"))

    MOCK_MODE: bool = os.getenv("MAO_MOCK_MODE", "").lower() in ("true", "1", "yes")

    KNOWLEDGE_BASE_PATH: Path = DATA_DIR / "knowledge_base.json"
    CONCEPT_NETWORK_PATH: Path = DATA_DIR / "concept_network.json"
    SIGNATURES_PATH: Path = DATA_DIR / "cognitive_signatures.json"
    PERSONA_PATH: Path = DATA_DIR / "persona.yaml"

    RAG_TOP_K: int = int(os.getenv("MAO_RAG_TOP_K", "5"))
    SIGNATURE_MATCH_THRESHOLD: float = float(os.getenv("MAO_SIGNATURE_THRESHOLD", "0.15"))
    MAX_PROMPT_LENGTH: int = int(os.getenv("MAO_MAX_PROMPT_LENGTH", "3500"))

    @classmethod
    def is_mock_mode(cls) -> bool:
        return cls.MOCK_MODE or not cls.API_KEY.strip()


settings = Settings()
