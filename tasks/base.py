# Base task executor
from abc import ABC, abstractmethod
from typing import Dict
from scheduler.models import Task, TaskType


class TaskExecutor(ABC):
    _executors: Dict[TaskType, "TaskExecutor"] = {}
    
    @abstractmethod
    async def execute(self, task: Task) -> dict:
        pass
    
    @classmethod
    def register(cls, task_type: TaskType, executor: "TaskExecutor"):
        cls._executors[task_type] = executor
    
    @classmethod
    def get_executor(cls, task_type: TaskType) -> "TaskExecutor":
        executor = cls._executors.get(task_type)
        if not executor:
            raise ValueError(f"No executor registered for type: {task_type}")
        return executor

