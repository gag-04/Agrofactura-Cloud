"""FastAPI application entrypoint for billing-core-service."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.api.auth import router as auth_router
from src.api.customers import router as customers_router
from src.api.health import router as health_router
from src.api.invoices import router as invoices_router
from src.core.config import settings
from src.core.database import init_db

STATIC_INDEX_PATH = os.path.join(os.path.dirname(__file__), "static", "index.html")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables and seed demo data."""
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend transaccional y fiscal agrario de AgroFactura Cloud",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for mobile/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api/v1
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(invoices_router, prefix=settings.API_V1_STR)


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the AgroFactura Cloud interactive testing dashboard."""
    if os.path.exists(STATIC_INDEX_PATH):
        with open(STATIC_INDEX_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>AgroFactura Cloud</h1><p>UI no encontrada en /static/index.html</p>")


@app.get("/api")
def api_info():
    """API info endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "ui": "/",
    }
