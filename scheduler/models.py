# Task data models
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import croniter


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class TaskType(str, Enum):
    SCRAPER = "scraper"
    EMAIL = "email"
    CLEANUP = "cleanup"
    CUSTOM = "custom"


class Task(BaseModel):
    id: str
    name: str
    task_type: TaskType
    cron_expression: str
    enabled: bool = True
    status: TaskStatus = TaskStatus.PENDING
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = 300
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        try:
            croniter.croniter(v, datetime.now())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")
        return v
    
    def calculate_next_run(self) -> datetime:
        if not self.enabled:
            return datetime.now()
        
        now = datetime.now()
        cron = croniter.croniter(self.cron_expression, now)
        return cron.get_next(datetime)
    
    def update_next_run(self):
        self.next_run = self.calculate_next_run()
        self.updated_at = datetime.now()
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class TaskExecution(BaseModel):
    task_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: TaskStatus
    error: Optional[str] = None
    duration: Optional[float] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

