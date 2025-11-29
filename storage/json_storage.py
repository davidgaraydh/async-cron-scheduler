# JSON storage backend
import json
import logging
import os
from datetime import datetime
from typing import List, Optional
from scheduler.models import Task
from .base import StorageBackend
from config import settings
import aiofiles

logger = logging.getLogger(__name__)


class JSONStorage(StorageBackend):
    def __init__(self, file_path: str = None):
        self.file_path = file_path or settings.json_storage_path
        self._tasks: dict = {}
    
    async def initialize(self):
        os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)
        
        if os.path.exists(self.file_path):
            async with aiofiles.open(self.file_path, "r") as f:
                content = await f.read()
                if content:
                    data = json.loads(content)
                    for task_data in data.get("tasks", []):
                        task = Task(**task_data)
                        # Convert datetime strings to datetime objects
                        if isinstance(task.created_at, str):
                            task.created_at = datetime.fromisoformat(task.created_at)
                        if isinstance(task.updated_at, str):
                            task.updated_at = datetime.fromisoformat(task.updated_at)
                        if isinstance(task.last_run, str):
                            task.last_run = datetime.fromisoformat(task.last_run)
                        if isinstance(task.next_run, str):
                            task.next_run = datetime.fromisoformat(task.next_run)
                        self._tasks[task.id] = task
            logger.info(f"Loaded {len(self._tasks)} tasks from {self.file_path}")
        else:
            logger.info(f"JSON file doesn't exist, will create: {self.file_path}")
    
    async def _save_to_file(self):
        tasks_data = []
        for task in self._tasks.values():
            task_dict = task.model_dump()
            tasks_data.append(task_dict)
        
        data = {"tasks": tasks_data}
        async with aiofiles.open(self.file_path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def save_task(self, task: Task) -> None:
        self._tasks[task.id] = task
        await self._save_to_file()
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    
    async def get_all_tasks(self) -> List[Task]:
        return list(self._tasks.values())
    
    async def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            await self._save_to_file()
            return True
        return False

