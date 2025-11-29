# Entry point
import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=False,
    )

