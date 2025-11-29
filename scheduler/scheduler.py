# Main scheduler
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from .models import Task, TaskStatus, TaskExecution
from storage.base import StorageBackend
from tasks.base import TaskExecutor
from config import settings

logger = logging.getLogger(__name__)


class AsyncScheduler:
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "active_tasks": 0,
        }
    
    async def start(self):
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        logger.info("Starting scheduler...")
        await self.load_tasks()
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")
    
    async def stop(self):
        if not self._running:
            return
        
        logger.info("Stopping scheduler...")
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Wait for running tasks to finish
        if self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} running tasks...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("Scheduler stopped")
    
    async def load_tasks(self):
        logger.info("Loading tasks from storage...")
        tasks = await self.storage.get_all_tasks()
        for task in tasks:
            task.update_next_run()
            self.tasks[task.id] = task
        logger.info(f"Loaded {len(self.tasks)} tasks")
    
    async def add_task(self, task: Task) -> Task:
        task.update_next_run()
        await self.storage.save_task(task)
        self.tasks[task.id] = task
        logger.info(f"Task added: {task.id} - {task.name}")
        return task
    
    async def remove_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        
        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        await self.storage.delete_task(task_id)
        del self.tasks[task_id]
        logger.info(f"Task removed: {task_id}")
        return True
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    async def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())
    
    async def _scheduler_loop(self):
        while self._running:
            try:
                await self._check_and_execute_tasks()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _check_and_execute_tasks(self):
        now = datetime.now()
        
        for task in self.tasks.values():
            if not task.enabled or task.status == TaskStatus.RUNNING:
                continue
            
            if task.next_run and task.next_run <= now:
                if task.id not in self.running_tasks:
                    asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: Task):
        async with self.semaphore:
            if task.id in self.running_tasks:
                return
            
            task.status = TaskStatus.RUNNING
            execution = TaskExecution(
                task_id=task.id,
                started_at=datetime.now(),
                status=TaskStatus.RUNNING
            )
            
            self.running_tasks[task.id] = asyncio.current_task()
            self.metrics["total_executions"] += 1
            self.metrics["active_tasks"] = len(self.running_tasks)
            
            try:
                logger.info(f"Running task: {task.id} - {task.name}")
                
                executor = TaskExecutor.get_executor(task.task_type)
                result = await asyncio.wait_for(
                    executor.execute(task),
                    timeout=task.timeout
                )
                
                execution.completed_at = datetime.now()
                execution.duration = (execution.completed_at - execution.started_at).total_seconds()
                execution.status = TaskStatus.COMPLETED
                
                task.status = TaskStatus.COMPLETED
                task.last_run = execution.started_at
                task.retry_count = 0
                self.metrics["successful_executions"] += 1
                
                logger.info(f"Task completed: {task.id} - Duration: {execution.duration:.2f}s")
                
            except asyncio.TimeoutError:
                execution.status = TaskStatus.FAILED
                execution.error = f"Timeout after {task.timeout}s"
                task.status = TaskStatus.FAILED
                logger.error(f"Task timeout: {task.id}")
                await self._handle_task_failure(task, execution)
                
            except Exception as e:
                execution.status = TaskStatus.FAILED
                execution.error = str(e)
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.id} failed: {e}", exc_info=True)
                await self._handle_task_failure(task, execution)
            
            finally:
                task.update_next_run()
                await self.storage.save_task(task)
                
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                
                self.metrics["active_tasks"] = len(self.running_tasks)
    
    async def _handle_task_failure(self, task: Task, execution: TaskExecution):
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            logger.info(f"Retrying task {task.id} ({task.retry_count}/{task.max_retries})")
            # Exponential backoff
            delay = min(2 ** task.retry_count, 60)
            await asyncio.sleep(delay)
            asyncio.create_task(self._execute_task(task))
        else:
            logger.error(f"Task {task.id} failed after {task.max_retries} attempts")
            task.status = TaskStatus.FAILED
            task.enabled = False
            self.metrics["failed_executions"] += 1
    
    def get_metrics(self) -> Dict:
        return {
            **self.metrics,
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "running_tasks": len(self.running_tasks),
        }

