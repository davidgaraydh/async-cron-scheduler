# Pydantic schemas for API
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from scheduler.models import TaskType, TaskStatus


class TaskCreate(BaseModel):
    name: str = Field(..., description="Task name")
    task_type: TaskType = Field(..., description="Task type: scraper, email, cleanup, custom")
    cron_expression: str = Field(..., description="Cron expression (format: * * * * *)")
    enabled: bool = Field(True, description="Whether the task is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Task-specific configuration")
    timeout: int = Field(300, description="Timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Daily scraper",
                    "task_type": "scraper",
                    "cron_expression": "0 9 * * *",
                    "enabled": True,
                    "config": {
                        "url": "https://example.com/api/data",
                        "method": "GET",
                        "headers": {
                            "Authorization": "Bearer token123"
                        },
                        "timeout": 30
                    },
                    "timeout": 300,
                    "max_retries": 3
                },
                {
                    "name": "Daily email",
                    "task_type": "email",
                    "cron_expression": "0 8 * * *",
                    "enabled": True,
                    "config": {
                        "to": "user@example.com",
                        "subject": "Daily report",
                        "body": "Email content here",
                        "smtp_host": "smtp.gmail.com",
                        "smtp_port": 587,
                        "smtp_user": "sender@gmail.com",
                        "smtp_password": "your_password",
                        "from": "sender@gmail.com"
                    },
                    "timeout": 300,
                    "max_retries": 3
                },
                {
                    "name": "Log cleanup",
                    "task_type": "cleanup",
                    "cron_expression": "0 2 * * *",
                    "enabled": True,
                    "config": {
                        "path": "/var/log",
                        "pattern": "*.log",
                        "max_age_days": 7,
                        "dry_run": False
                    },
                    "timeout": 300,
                    "max_retries": 3
                },
                {
                    "name": "Custom task",
                    "task_type": "custom",
                    "cron_expression": "0 * * * *",
                    "enabled": True,
                    "config": {
                        "module": "my_module",
                        "function": "my_function"
                    },
                    "timeout": 300,
                    "max_retries": 3
                }
            ]
        }
    )


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New task name")
    cron_expression: Optional[str] = Field(None, description="New cron expression")
    enabled: Optional[bool] = Field(None, description="Enable or disable the task")
    config: Optional[Dict[str, Any]] = Field(None, description="New configuration")
    timeout: Optional[int] = Field(None, description="New timeout in seconds")
    max_retries: Optional[int] = Field(None, description="New maximum retries")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "enabled": False,
                    "cron_expression": "0 10 * * *"
                },
                {
                    "name": "New task name",
                    "timeout": 600,
                    "max_retries": 5
                },
                {
                    "config": {
                        "url": "https://new-url.com",
                        "method": "POST"
                    }
                }
            ]
        }
    )


class TaskResponse(BaseModel):
    id: str
    name: str
    task_type: TaskType
    cron_expression: str
    enabled: bool
    status: TaskStatus
    config: Dict[str, Any]
    timeout: int
    max_retries: int
    retry_count: int
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    scheduler_running: bool
    timestamp: datetime


class MetricsResponse(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    active_tasks: int
    total_tasks: int
    enabled_tasks: int
    running_tasks: int

