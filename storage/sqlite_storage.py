# SQLite storage backend
import aiosqlite
import json
import logging
from datetime import datetime
from typing import List, Optional
from scheduler.models import Task, TaskStatus, TaskType
from .base import StorageBackend
from config import settings

logger = logging.getLogger(__name__)


class SQLiteStorage(StorageBackend):
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._db: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        import os
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                cron_expression TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                status TEXT NOT NULL,
                config TEXT NOT NULL,
                timeout INTEGER NOT NULL,
                max_retries INTEGER NOT NULL,
                retry_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_run TEXT,
                next_run TEXT
            )
        """)
        await self._db.commit()
        logger.info(f"SQLite database initialized: {self.db_path}")
    
    async def save_task(self, task: Task) -> None:
        await self._db.execute("""
            INSERT OR REPLACE INTO tasks 
            (id, name, task_type, cron_expression, enabled, status, config,
             timeout, max_retries, retry_count, created_at, updated_at, last_run, next_run)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.name,
            task.task_type.value,
            task.cron_expression,
            1 if task.enabled else 0,
            task.status.value,
            json.dumps(task.config),
            task.timeout,
            task.max_retries,
            task.retry_count,
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
            task.last_run.isoformat() if task.last_run else None,
            task.next_run.isoformat() if task.next_run else None,
        ))
        await self._db.commit()
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        async with self._db.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_task(row)
    
    async def get_all_tasks(self) -> List[Task]:
        tasks = []
        async with self._db.execute("SELECT * FROM tasks") as cursor:
            async for row in cursor:
                tasks.append(self._row_to_task(row))
        return tasks
    
    async def delete_task(self, task_id: str) -> bool:
        cursor = await self._db.execute(
            "DELETE FROM tasks WHERE id = ?", (task_id,)
        )
        await self._db.commit()
        return cursor.rowcount > 0
    
    def _row_to_task(self, row) -> Task:
        return Task(
            id=row[0],
            name=row[1],
            task_type=TaskType(row[2]),
            cron_expression=row[3],
            enabled=bool(row[4]),
            status=TaskStatus(row[5]),
            config=json.loads(row[6]),
            timeout=row[7],
            max_retries=row[8],
            retry_count=row[9],
            created_at=datetime.fromisoformat(row[10]),
            updated_at=datetime.fromisoformat(row[11]),
            last_run=datetime.fromisoformat(row[12]) if row[12] else None,
            next_run=datetime.fromisoformat(row[13]) if row[13] else None,
        )
    
    async def close(self):
        if self._db:
            await self._db.close()

