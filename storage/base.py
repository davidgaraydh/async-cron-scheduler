"""Interfaz base para backends de almacenamiento."""
from abc import ABC, abstractmethod
from typing import List, Optional
from scheduler.models import Task


class StorageBackend(ABC):
    @abstractmethod
    async def save_task(self, task: Task) -> None:
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        pass
    
    @abstractmethod
    async def get_all_tasks(self) -> List[Task]:
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        pass

