"""
Main FastAPI application with OpenAPI/Swagger documentation.
This is the entry point for the AI Cost Monitoring Platform API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.api.v1 import auth, rate_limits
from app.cron.rate_limits_fetcher import fetch_all_rate_limits

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="B2B AI cost-monitoring platform with secure JWT authentication and tenant isolation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    rate_limits.router,
    prefix="/api/v1",
    tags=["Rate Limits"]
)


# Initialize background scheduler for cron jobs
scheduler = BackgroundScheduler()


@app.on_event("startup")
async def startup_event():
    """Initialize scheduled tasks on application startup."""
    # Schedule rate limits fetch job to run every 15 minutes
    scheduler.add_job(
        fetch_all_rate_limits,
        'interval',
        minutes=15,
        id='rate_limits_fetch',
        replace_existing=True
    )
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler on application shutdown."""
    scheduler.shutdown()


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "AI Cost Monitoring Platform API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
