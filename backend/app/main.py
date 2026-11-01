import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.services.db import init_db
from backend.app.workers.queue_worker import get_queue_worker
from backend.app.api.routes import webhook, auth, dashboard, queue

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    worker = get_queue_worker()
    worker.start()
    logger.info("Munim AI system & background QueueWorker initialized.")
    yield
    # Shutdown actions
    await worker.stop()
    logger.info("Munim AI background QueueWorker stopped.")

app = FastAPI(
    title="Munim AI Backend",
    description="WhatsApp Assistant & Self-updating Ledger for Small Sellers",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS restricted to configured origins (prevents wildcard + credentials security conflict)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(webhook.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(queue.router)


@app.get("/")
async def root():
    return {
        "app": "Munim AI",
        "status": "healthy",
        "env": settings.APP_ENV
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
