# Application configuration
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_key: str = "your-secret-api-key-here"
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    # Storage Configuration
    storage_type: Literal["sqlite", "json"] = "sqlite"
    sqlite_db_path: str = "./data/scheduler.db"
    json_storage_path: str = "./data/tasks.json"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Scheduler Configuration
    max_concurrent_tasks: int = 10
    default_task_timeout: int = 300
    default_max_retries: int = 3


settings = Settings()

