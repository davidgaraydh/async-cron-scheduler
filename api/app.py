# FastAPI app
import logging
import uuid
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from scheduler.models import Task, TaskType
from scheduler.scheduler import AsyncScheduler
from storage.sqlite_storage import SQLiteStorage
from storage.json_storage import JSONStorage
from storage.base import StorageBackend
from tasks.scraper_task import ScraperTaskExecutor
from tasks.email_task import EmailTaskExecutor
from tasks.cleanup_task import CleanupTaskExecutor
from tasks.custom_task import CustomTaskExecutor
from tasks.base import TaskExecutor
from config import settings
from .schemas import (
    TaskCreate, TaskUpdate, TaskResponse, HealthResponse, MetricsResponse
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}' if settings.log_format == "json" else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Async Cron Scheduler API",
    description="API REST for managing scheduled tasks with cron expressions",
    version="1.0.0"
)

# Global scheduler and storage
scheduler: AsyncScheduler = None
storage: StorageBackend = None


@app.on_event("startup")
async def startup_event():
    global scheduler, storage
    
    logger.info("Starting up...")
    
    # Setup storage
    if settings.storage_type == "sqlite":
        storage = SQLiteStorage()
    else:
        storage = JSONStorage()
    
    await storage.initialize()
    
    # Create scheduler
    scheduler = AsyncScheduler(storage)
    
    # Register task executors
    TaskExecutor.register(TaskType.SCRAPER, ScraperTaskExecutor())
    TaskExecutor.register(TaskType.EMAIL, EmailTaskExecutor())
    TaskExecutor.register(TaskType.CLEANUP, CleanupTaskExecutor())
    TaskExecutor.register(TaskType.CUSTOM, CustomTaskExecutor())
    
    # Start scheduler
    await scheduler.start()
    
    logger.info("Ready")


@app.on_event("shutdown")
async def shutdown_event():
    global scheduler
    
    logger.info("Shutting down...")
    
    if scheduler:
        await scheduler.stop()
    
    if storage and hasattr(storage, "close"):
        await storage.close()
    
    logger.info("Shutdown complete")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check if the service is running."""
    return HealthResponse(
        status="healthy",
        scheduler_running=scheduler._running if scheduler else False,
        timestamp=datetime.now()
    )


@app.get("/metrics", response_model=MetricsResponse, tags=["Metrics"])
async def get_metrics():
    """Get scheduler stats."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    metrics = scheduler.get_metrics()
    return MetricsResponse(**metrics)


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
async def create_task(task_data: TaskCreate):
    """Create a new scheduled task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    try:
        task = Task(
            id=str(uuid.uuid4()),
            name=task_data.name,
            task_type=task_data.task_type,
            cron_expression=task_data.cron_expression,
            enabled=task_data.enabled,
            config=task_data.config,
            timeout=task_data.timeout,
            max_retries=task_data.max_retries,
        )
        
        task = await scheduler.add_task(task)
        logger.info(f"Task created: {task.id} - {task.name}")
        
        return TaskResponse(**task.model_dump())
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def list_tasks():
    """Get all tasks."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    tasks = await scheduler.get_all_tasks()
    return [TaskResponse(**task.model_dump()) for task in tasks]


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(task_id: str):
    """Get a task by ID."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    task = await scheduler.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**task.model_dump())


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(task_id: str, task_data: TaskUpdate):
    """Update a task. All fields are optional."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    task = await scheduler.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.cron_expression is not None:
            task.cron_expression = task_data.cron_expression
            task.update_next_run()
        if task_data.enabled is not None:
            task.enabled = task_data.enabled
        if task_data.config is not None:
            task.config = task_data.config
        if task_data.timeout is not None:
            task.timeout = task_data.timeout
        if task_data.max_retries is not None:
            task.max_retries = task_data.max_retries
        
        task = await scheduler.add_task(task)
        logger.info(f"Task updated: {task.id}")
        
        return TaskResponse(**task.model_dump())
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
async def delete_task(task_id: str):
    """Delete a task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    deleted = await scheduler.remove_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"Task deleted: {task_id}")
    return JSONResponse(status_code=204, content=None)

