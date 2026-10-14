"""应用配置：从 .env 读取，缺省值见下方。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 存储
    chroma_dir: str = "./chroma_db"
    docs_dir: str = "./docs"
    collection_name: str = "knyx"

    # 分块与检索
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 4
    similarity_threshold: float = 0.5
    history_turns: int = 4

    # LLM（OpenAI 兼容 Chat Completions）
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    # Embedding（api | local）
    embedding_provider: str = "api"
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_api_key: str = ""
    embedding_model: str = "BAAI/bge-m3"
    embedding_local_model: str = "BAAI/bge-small-zh-v1.5"


settings = Settings()
