import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .routers import auth, contracts
from .db.session import init_db

app = FastAPI(
    title="Contract Evaluation API",
    description="API for analyzing and evaluating smart contracts",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])

@app.on_event("startup")
async def startup_event():
    # Initialize database
    await init_db()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
