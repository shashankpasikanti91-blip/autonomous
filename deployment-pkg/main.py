"""
Main entry point for the platform.
"""
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from api.main import app

if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload if settings.debug else False,
        log_level=settings.log_level.lower()
    )
