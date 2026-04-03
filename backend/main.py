"""
ScholarGraph AI — FastAPI Application Entry Point
Production-grade academic intelligence platform.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_settings
from database.session import init_db
from api.routes_upload import router as upload_router
from api.routes_predict import router as predict_router
from api.routes_quiz import router as quiz_router
from api.routes_graph import router as graph_router
from api.routes_dashboard import router as dashboard_router
from api.routes_chat import router as chat_router
from auth.jwt_handler import router as auth_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # ── Startup ──
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    init_db()
    print("Database initialized")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"Upload directory ready: {settings.UPLOAD_DIR}")

    yield

    # Shutdown
    print("Shutting down ScholarGraph AI")


# ── FastAPI App ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "GenAI-powered academic intelligence platform. "
        "Analyze syllabi, past year questions, and lecture notes to predict "
        "exam topics with probability scores, generate knowledge graphs, "
        "adaptive quizzes, and personalized study plans."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route Registration ──────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api/upload", tags=["Document Upload"])
app.include_router(predict_router, prefix="/api/predict", tags=["Prediction"])
app.include_router(quiz_router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(graph_router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check with component status."""
    return {
        "status": "healthy",
        "components": {
            "database": "connected",
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "llm_model": settings.OPENAI_MODEL,
            "vector_db": "pinecone",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
