from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import todos
from app.config import get_settings
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Xain Todo API",
    description="Real-time backend",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


app.include_router(todos.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.1",
        "service": "hierarchical-todo-api"
    }

@app.get("/")
async def root():
    return {
        "message": "Backend links",
        "docs": "/docs",
        "health": "/health"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting...")
    logger.info(f"API Documentation: http://localhost:{settings.backend_port}/docs")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True,
        log_level="info"
    )
