"""
FastAPI Application - AYA Insurance Agent
Point d'entrée principal de l'application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.api import chat, payment_webhook
import logging
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API pour AYA - Conseillère digitale IA NSIA Assurances",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(chat.router, prefix="/api", tags=["Agent"])
app.include_router(payment_webhook.router, prefix="/api/payment", tags=["Payment"])


@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "AYA Insurance Agent API"
    }


@app.get("/test")
async def test_interface():
    """Endpoint pour l'interface de test"""
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "test-interface.html")
    return FileResponse(static_path)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'application"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} démarré")
    logger.info(f"📊 Mode DEBUG: {settings.DEBUG}")
    logger.info(f"🔗 Base Webhook URL: {settings.BASE_WEBHOOK_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions à l'arrêt de l'application"""
    logger.info(f"🛑 {settings.APP_NAME} arrêté")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
