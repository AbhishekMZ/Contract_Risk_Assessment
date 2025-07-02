from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, analysis, contracts
from .core.config import settings

app = FastAPI(
    title="Contract Evaluation API",
    description="API for smart contract analysis and evaluation",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
