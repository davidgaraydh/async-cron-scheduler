# Custom task executor
import asyncio
import logging
import importlib
from typing import Dict
from scheduler.models import Task
from .base import TaskExecutor

logger = logging.getLogger(__name__)


class CustomTaskExecutor(TaskExecutor):
    async def execute(self, task: Task) -> dict:
        module_path = task.config.get("module")
        function_name = task.config.get("function")
        
        if not module_path or not function_name:
            raise ValueError("module and function must be specified in config")
        
        logger.info(f"Running custom task: {module_path}.{function_name}")
        
        try:
            module = importlib.import_module(module_path)
            function = getattr(module, function_name)
            
            if not callable(function):
                raise ValueError(f"{function_name} is not a function")
            
            if asyncio.iscoroutinefunction(function):
                result = await function(task.config)
            else:
                result = function(task.config)
            
            logger.info(f"Custom task completed: {module_path}.{function_name}")
            return {"status": "completed", "result": result}
            
        except Exception as e:
            logger.error(f"Custom task failed: {e}", exc_info=True)
            raise

