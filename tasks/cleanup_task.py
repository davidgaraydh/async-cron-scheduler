# File cleanup task executor
import logging
import os
import glob
import asyncio
from typing import Dict
from scheduler.models import Task
from .base import TaskExecutor

logger = logging.getLogger(__name__)


class CleanupTaskExecutor(TaskExecutor):
    async def execute(self, task: Task) -> dict:
        path = task.config.get("path")
        pattern = task.config.get("pattern", "*")
        max_age_days = task.config.get("max_age_days")
        dry_run = task.config.get("dry_run", False)
        
        if not path:
            raise ValueError("Path not specified in config")
        
        logger.info(f"Cleanup: {path}/{pattern}")
        
        full_pattern = os.path.join(path, pattern)
        files_to_delete = []
        total_size = 0
        
        for file_path in glob.glob(full_pattern, recursive=True):
            if os.path.isfile(file_path):
                if max_age_days:
                    file_age = (asyncio.get_event_loop().time() - os.path.getmtime(file_path)) / 86400
                    if file_age < max_age_days:
                        continue
                
                files_to_delete.append(file_path)
                total_size += os.path.getsize(file_path)
        
        deleted_count = 0
        deleted_size = 0
        
        if not dry_run:
            for file_path in files_to_delete:
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_size += file_size
                    logger.debug(f"Deleted: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
        else:
            logger.info(f"DRY RUN: Would delete {len(files_to_delete)} files")
        
        result = {
            "files_found": len(files_to_delete),
            "files_deleted": deleted_count if not dry_run else 0,
            "total_size_bytes": total_size,
            "deleted_size_bytes": deleted_size if not dry_run else 0,
            "dry_run": dry_run,
        }
        
        logger.info(f"Cleanup done: {deleted_count} files deleted")
        return result

