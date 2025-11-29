# Async Cron Scheduler

A Python task scheduler that runs jobs on a schedule using cron expressions. It's async, supports multiple task types, and stores everything in SQLite or JSON. Basically cron but with a REST API and better error handling.

## What it does

I built this because I needed something to run scheduled tasks (API checks, email reports, file cleanup, etc.) but wanted more control than regular cron. It's basically a cron replacement that:

- Runs tasks based on cron expressions
- Executes multiple tasks concurrently with asyncio
- Persists tasks to SQLite or JSON (survives restarts)
- Has a REST API to manage tasks
- Supports different task types (HTTP requests, emails, file cleanup, custom functions)
- Handles retries and timeouts automatically

## Requirements

- Python 3.11+
- pip

## Installation

Clone the repo:

```bash
git clone <repo-url>
cd async-cron-scheduler
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set up the config file:

```bash
# Linux/Mac
cp .env.example .env

# Windows
copy .env.example .env
```

You can edit `.env` if you want, but the defaults should work fine.

## Running it

Just run:

```bash
python main.py
```

You'll see something like:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
{"timestamp": "2025-11-29 10:00:00", "level": "INFO", "message": "Initializing application...", "module": "api.app"}
{"timestamp": "2025-11-29 10:00:00", "level": "INFO", "message": "SQLite database initialized: ./data/scheduler.db", "module": "storage.sqlite_storage"}
{"timestamp": "2025-11-29 10:00:00", "level": "INFO", "message": "Scheduler started", "module": "scheduler.scheduler"}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Server runs on `http://localhost:8000`. The API docs are at:
- `http://localhost:8000/docs` (Swagger)
- `http://localhost:8000/redoc` (ReDoc)

## Configuration

All config is in `.env`. The `.env.example` file has all the options. Here's what you can change:

- `API_KEY` - Not used right now, but there if you need it later
- `API_PORT` - Port for the API (default: 8000)
- `API_HOST` - Host to bind to (default: 0.0.0.0)
- `STORAGE_TYPE` - `sqlite` or `json` (default: sqlite)
- `SQLITE_DB_PATH` - Where to store the SQLite DB
- `JSON_STORAGE_PATH` - Where to store the JSON file (if using json storage)
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR (default: INFO)
- `LOG_FORMAT` - `json` or `text` (default: json)
- `MAX_CONCURRENT_TASKS` - How many tasks can run at once (default: 10)
- `DEFAULT_TASK_TIMEOUT` - Task timeout in seconds (default: 300)
- `DEFAULT_MAX_RETRIES` - How many times to retry failed tasks (default: 3)

The `.env` file is gitignored, so your secrets stay local.

## API Endpoints

### Health check

```
GET /health
```

Returns if the service is up and if the scheduler is running.

### Create task

```
POST /tasks
Content-Type: application/json

{
  "name": "Daily scraper",
  "task_type": "scraper",
  "cron_expression": "0 9 * * *",
  "enabled": true,
  "config": {
    "url": "https://example.com/api/data",
    "method": "GET"
  },
  "timeout": 300,
  "max_retries": 3
}
```

### List tasks

```
GET /tasks
```

Returns all tasks.

### Get task

```
GET /tasks/{task_id}
```

Get a specific task by ID.

### Update task

```
PUT /tasks/{task_id}
Content-Type: application/json

{
  "enabled": false,
  "cron_expression": "0 10 * * *"
}
```

All fields are optional - only update what you need.

### Delete task

```
DELETE /tasks/{task_id}
```

### Metrics

```
GET /metrics
```

Returns stats about task executions, success/failure counts, etc.

## Task Types

### Scraper

Makes HTTP requests. Good for checking APIs, scraping data, or health checks.

Example:

```json
{
  "name": "API Health Check",
  "task_type": "scraper",
  "cron_expression": "*/5 * * * *",
  "enabled": true,
  "config": {
    "url": "https://api.example.com/health",
    "method": "GET",
    "headers": {
      "Authorization": "Bearer your-token"
    },
    "timeout": 30
  }
}
```

### Email

Sends emails via SMTP. Useful for reports or notifications.

Example:

```json
{
  "name": "Daily Report",
  "task_type": "email",
  "cron_expression": "0 8 * * *",
  "enabled": true,
  "config": {
    "to": "recipient@example.com",
    "subject": "Daily Report",
    "body": "Report content here",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "sender@gmail.com",
    "smtp_password": "your-password",
    "from": "sender@gmail.com"
  }
}
```

### Cleanup

Deletes files based on pattern and age. Handy for cleaning up logs or temp files.

Example:

```json
{
  "name": "Log Cleanup",
  "task_type": "cleanup",
  "cron_expression": "0 2 * * *",
  "enabled": true,
  "config": {
    "path": "/var/log",
    "pattern": "*.log",
    "max_age_days": 7,
    "dry_run": false
  }
}
```

Set `dry_run: true` to see what would be deleted without actually deleting.

### Custom

Runs your own Python functions. Put your function in a module and reference it.

Example:

```json
{
  "name": "Custom Processing",
  "task_type": "custom",
  "cron_expression": "0 * * * *",
  "enabled": true,
  "config": {
    "module": "my_module",
    "function": "my_function"
  }
}
```

The function should accept the task config as a parameter. Can be async or sync.

## Cron Expressions

Standard 5-field cron format:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 and 7 = Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

Some examples:

- `0 9 * * *` - Every day at 9 AM
- `*/5 * * * *` - Every 5 minutes
- `0 0 * * 0` - Every Sunday at midnight
- `0 0 1 * *` - First day of each month at midnight
- `0 */2 * * *` - Every 2 hours
- `30 14 * * 1-5` - Weekdays at 2:30 PM

## Project Structure

```
async-cron-scheduler/
├── api/              # FastAPI app
│   ├── app.py
│   ├── auth.py
│   └── schemas.py
├── scheduler/        # Core scheduler
│   ├── scheduler.py
│   └── models.py
├── storage/          # Storage backends
│   ├── base.py
│   ├── sqlite_storage.py
│   └── json_storage.py
├── tasks/            # Task executors
│   ├── base.py
│   ├── scraper_task.py
│   ├── email_task.py
│   ├── cleanup_task.py
│   └── custom_task.py
├── config.py
├── main.py
└── requirements.txt
```

## Adding Custom Task Types

The code is modular, so adding new task types is straightforward:

1. Create a new file in `tasks/` that inherits from `TaskExecutor`
2. Implement the `execute()` method
3. Register it in `api/app.py` during startup

Example:

```python
# tasks/my_task.py
from .base import TaskExecutor
from scheduler.models import Task

class MyTaskExecutor(TaskExecutor):
    async def execute(self, task: Task) -> dict:
        config = task.config
        # Do your thing here
        return {"status": "completed"}
```

Then in `api/app.py`:

```python
from tasks.my_task import MyTaskExecutor

@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    TaskExecutor.register(TaskType.CUSTOM, MyTaskExecutor())
```

## Logging

Logs are configured via `.env`:

- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_FORMAT` - `json` or `text`

JSON format is useful if you're using log aggregation tools.

## Security Notes

Right now the API is public (no auth required). If you're exposing this to the internet, you probably want to add authentication or put it behind a reverse proxy.

Tasks have timeouts to prevent them from hanging forever. Cron expressions are validated before saving.

## Troubleshooting

**Scheduler won't start:**
- Check that `.env` exists
- Make sure `data/` directory exists and is writable
- Look at the logs for errors

**Tasks not running:**
- Make sure tasks have `enabled: true`
- Check that cron expressions are valid
- Verify scheduler is running (hit `/health` endpoint)
- Check logs for execution errors

**Database errors:**
- SQLite: check file permissions
- JSON: make sure directory exists
- Both: ensure `data/` is writable

**Task execution fails:**
- Check your config (URLs, credentials, file paths)
- Look at logs for specific errors
- For scrapers: verify network connectivity
- For emails: check SMTP settings
- For cleanup: make sure paths exist

## Quick Example

1. Start the server:
   ```bash
   python main.py
   ```

2. Create a task:
   ```bash
   curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "API Check",
       "task_type": "scraper",
       "cron_expression": "0 9 * * *",
       "enabled": true,
       "config": {
         "url": "https://api.example.com/health",
         "method": "GET"
       }
     }'
   ```

3. Check tasks:
   ```bash
   curl "http://localhost:8000/tasks"
   ```

4. View metrics:
   ```bash
   curl "http://localhost:8000/metrics"
   ```
