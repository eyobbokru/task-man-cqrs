from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI


from core.config import get_settings
from core.logging import setup_logging
from infrastructure.database import close_db, init_db

from api.routes import workspace_routes

settings = get_settings()
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

app.include_router(workspace_routes.router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)