import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
<<<<<<< Updated upstream
from backend.app.api.error_handlers import register_exception_handlers
from backend.app.api.routes import (
    webhook,
    auth,
    dashboard,
    customers,
    products,
    inventory,
    orders,
    payments,
    media,
)
=======
from backend.app.api.routes import webhook, auth, dashboard
>>>>>>> Stashed changes

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="Munim AI Backend",
    description="WhatsApp Assistant & Self-updating Ledger for Small Sellers",
    version="1.0.0"
)

<<<<<<< Updated upstream
# Register domain and repository exception handlers
register_exception_handlers(app)

=======
>>>>>>> Stashed changes
# Enable CORS restricted to configured origins (prevents wildcard + credentials security conflict)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< Updated upstream
# Include core and webhook routes
=======
# Include API routes
>>>>>>> Stashed changes
app.include_router(webhook.router)
app.include_router(auth.router)
app.include_router(dashboard.router)

<<<<<<< Updated upstream
# Include Phase 3E resource routes
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(media.router)

# Also expose dashboard under /api/dashboard for unified API gateway prefixing
app.include_router(dashboard.router, prefix="/api")

=======
>>>>>>> Stashed changes

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
