# HTTP scraper task executor
import logging
import aiohttp
from typing import Dict
from scheduler.models import Task
from .base import TaskExecutor

logger = logging.getLogger(__name__)


class ScraperTaskExecutor(TaskExecutor):
    async def execute(self, task: Task) -> dict:
        url = task.config.get("url")
        if not url:
            raise ValueError("URL not specified in config")
        
        method = task.config.get("method", "GET")
        headers = task.config.get("headers", {})
        timeout = task.config.get("timeout", 30)
        
        logger.info(f"Scraping: {method} {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                status = response.status
                content = await response.text()
                
                result = {
                    "status_code": status,
                    "content_length": len(content),
                    "url": url,
                }
                
                # TODO: add CSS selector support if needed
                if "css_selector" in task.config:
                    pass
                
                logger.info(f"Scraper done: {url} - Status: {status}")
                return result

