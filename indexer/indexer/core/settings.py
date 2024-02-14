from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pg_dsn: str = 'postgresql+asyncpg://localhost:5432/ton_index_a'
    api_root_path: str = ''
    api_title: str = ''
    ton_http_api_endpoint: str = ''

    cache_endpoint: Optional[str] = None

    class Config:
        env_prefix = 'ton_indexer_'
