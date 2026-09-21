from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings, Environment
from backend.api.router import api_router
from backend.core.database import engine, Base

# Create all tables in the database ONLY if not in production
if settings.ENVIRONMENT != Environment.PRODUCTION:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.ENVIRONMENT != Environment.PRODUCTION else None, # Disable swagger in prod if wanted, but standard is to keep it or just disable debug
    redoc_url="/redoc" if settings.ENVIRONMENT != Environment.PRODUCTION else None
)

from fastapi.responses import JSONResponse
from fastapi import Request
import logging

logger = logging.getLogger("markmint")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler ensuring production safety and reliable CORS headers."""
    logger.exception("Unhandled server error during %s %s: %s", request.method, request.url.path, exc)
    
    if settings.ENVIRONMENT == Environment.PRODUCTION:
        detail = "An internal server error occurred while processing your request. Please try again later."
    else:
        detail = str(exc)

    response = JSONResponse(
        status_code=500,
        content={"detail": detail}
    )
    
    # Guarantee CORS headers on 500 error responses
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
    elif settings.CORS_ORIGINS:
        first_origin = settings.CORS_ORIGINS[0] if isinstance(settings.CORS_ORIGINS, list) else settings.CORS_ORIGINS
        if first_origin != "*":
            response.headers["Access-Control-Allow-Origin"] = first_origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"

    return response

@app.get("/health", tags=["Health"])
@app.head("/health", tags=["Health"])
def health_check():
    """Lightweight health endpoint."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.on_event("startup")
def on_startup():
    try:
        from backend.core.database import SessionLocal
        from backend.services.curriculum_seeder import ensure_curriculum_seeded
        db = SessionLocal()
        try:
            ensure_curriculum_seeded(db)
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger("markmint").warning("Startup curriculum seeding deferred: %s", e)

app.include_router(api_router, prefix="/api")
