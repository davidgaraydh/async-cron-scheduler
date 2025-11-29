# Email task executor
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from scheduler.models import Task
from .base import TaskExecutor

logger = logging.getLogger(__name__)


class EmailTaskExecutor(TaskExecutor):
    async def execute(self, task: Task) -> dict:
        to = task.config.get("to")
        subject = task.config.get("subject", "")
        body = task.config.get("body", "")
        smtp_host = task.config.get("smtp_host", "localhost")
        smtp_port = task.config.get("smtp_port", 587)
        smtp_user = task.config.get("smtp_user")
        smtp_password = task.config.get("smtp_password")
        from_email = task.config.get("from", smtp_user)
        
        if not to:
            raise ValueError("Recipient not specified")
        
        logger.info(f"Sending email to: {to}")
        
        # Run in thread pool since smtplib is sync
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._send_email_sync,
            smtp_host,
            smtp_port,
            smtp_user,
            smtp_password,
            from_email,
            to,
            subject,
            body
        )
        
        logger.info(f"Email sent to: {to}")
        return {"status": "sent", "to": to, "subject": subject}
    
    def _send_email_sync(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to: str,
        subject: str,
        body: str
    ):
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

