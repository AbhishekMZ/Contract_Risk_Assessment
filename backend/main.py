from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from core.vulnerability_detector import Severity
from typing import Optional, List, Dict, Any
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Import analysis modules
from core.vulnerability_detector import VulnerabilityDetector
from core.analysis.utils import (
    calculate_file_hash,
    save_analysis_results,
    load_analysis_results,
    count_vulnerabilities_by_severity
)

# Initialize vulnerability detector
vulnerability_detector = VulnerabilityDetector()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings
class Settings(BaseSettings):
    app_name: str = "Smart Contract Analyzer API"
    app_version: str = "0.1.0"
    upload_folder: str = "uploads"
    results_folder: str = "results"
    allowed_extensions: List[str] = [".sol"]
    max_file_size: int = 16 * 1024 * 1024  # 16MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure upload and results directories exist
os.makedirs(settings.upload_folder, exist_ok=True)
os.makedirs(settings.results_folder, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for analyzing smart contract vulnerabilities"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class AnalysisResult(BaseModel):
    id: str
    filename: str
    status: str
    timestamp: str
    vulnerabilities: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {
        "total": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
    }
    file_hash: Optional[str] = None
    success: bool = True

class AnalysisStatus(BaseModel):
    id: str
    status: str
    progress: int = 0
    message: Optional[str] = None

class AnalysisRequest(BaseModel):
    contract_code: Optional[str] = None
    file_id: Optional[str] = None

# In-memory storage for analysis status (in production, use a database)
analysis_status: Dict[str, AnalysisStatus] = {}

# Helper functions
def analyze_contract_sync(file_path: str, analysis_id: str):
    """Synchronous function to analyze a contract"""
    try:
        logger.info(f"Starting analysis for {analysis_id} with file {file_path}")
        # Initialize status
        analysis_status[analysis_id] = AnalysisStatus(
            id=analysis_id,
            status="processing",
            progress=10,
            message="Starting analysis..."
        )
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Contract file not found at {file_path}")
            
        # Read the contract content
        analysis_status[analysis_id].progress = 20
        analysis_status[analysis_id].message = "Reading contract file..."
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            logger.info(f"Successfully read {len(source_code)} bytes from {file_path}")
        except UnicodeDecodeError:
            # Try different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin1') as f:
                source_code = f.read()
            logger.info(f"Used latin1 encoding to read {len(source_code)} bytes from {file_path}")
        
        # Check if content is empty
        if not source_code or len(source_code.strip()) == 0:
            raise ValueError(f"Contract file is empty at {file_path}")
        
        # Run vulnerability detection
        analysis_status[analysis_id].progress = 40
        analysis_status[analysis_id].message = "Detecting vulnerabilities..."
        logger.info(f"Running vulnerability detection for {analysis_id}")
        vulnerabilities = vulnerability_detector.detect_vulnerabilities(source_code)
        logger.info(f"Found {len(vulnerabilities)} vulnerabilities for {analysis_id}")
        
        # Count vulnerabilities by severity
        severity_counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln["severity"]
            if isinstance(severity, Severity):
                severity = severity.value
            severity_counts[severity] += 1
        
        # Prepare analysis result
        analysis_result = {
            "id": analysis_id,
            "filename": os.path.basename(file_path),
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "vulnerabilities": vulnerabilities,
            "stats": {
                "total": len(vulnerabilities),
                **severity_counts,
            },
            "file_hash": calculate_file_hash(file_path),
            "success": True
        }
        
        # Save the result
        analysis_status[analysis_id].progress = 80
        analysis_status[analysis_id].message = "Saving analysis results..."
        result_file = os.path.join(settings.results_folder, f"{analysis_id}.json")
        logger.info(f"Saving analysis result to {result_file}")
        
        # Use the improved save_analysis_results function which handles atomic writes
        try:
            save_analysis_results(analysis_result, result_file)
            logger.info(f"Successfully saved analysis result to {result_file}")
        except Exception as save_error:
            logger.error(f"Error saving analysis result: {str(save_error)}")
            raise

        # Final status update (after file is safely written)
        analysis_status[analysis_id].status = "completed"
        analysis_status[analysis_id].progress = 100
        analysis_status[analysis_id].message = "Analysis completed successfully"
        logger.info(f"Analysis {analysis_id} completed successfully")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing contract {analysis_id}: {str(e)}")
        if analysis_id in analysis_status:
            analysis_status[analysis_id].status = "failed"
            analysis_status[analysis_id].progress = 0
            analysis_status[analysis_id].message = f"Analysis failed: {str(e)}"
        raise

# Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Smart Contract Analyzer API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "running"
    }

@app.post("/api/upload", response_model=Dict[str, str])
async def upload_contract(file: UploadFile = File(...)):
    """Upload a smart contract file for analysis"""
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_folder, f"{file_id}{file_ext}")
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    return {"id": file_id, "filename": file.filename}

@app.post("/api/analyze", response_model=AnalysisStatus)
async def analyze_contract(
    background_tasks: BackgroundTasks,
    contract: Optional[str] = Form(None),
    file_id: Optional[str] = Form(None)
):
    """
    Analyze a smart contract for vulnerabilities.
    
    Either contract code or file_id must be provided.
    """
    if not contract and not file_id:
        raise HTTPException(
            status_code=400,
            detail="Either contract code or file_id must be provided"
        )
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis status
    status = AnalysisStatus(
        id=analysis_id,
        status="queued",
        progress=0,
        message="Analysis queued"
    )
    analysis_status[analysis_id] = status
    
    file_path = None
    
    try:
        if file_id:
            # Find the uploaded file - try with .sol extension first
            file_path = os.path.join(settings.upload_folder, f"{file_id}.sol")
            
            # If not found, check for other allowed extensions
            if not os.path.exists(file_path):
                file_path = None
                for ext in settings.allowed_extensions:
                    path = os.path.join(settings.upload_folder, f"{file_id}{ext}")
                    if os.path.exists(path):
                        file_path = path
                        break
            
            if not file_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"File with ID {file_id} not found"
                )
        
        elif contract:
            # Save contract code to a temporary file
            logger.info(f"Saving contract code to temporary file for analysis ID: {analysis_id}")
            file_path = os.path.join(settings.upload_folder, f"temp_{analysis_id}.sol")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(contract)
        
        # Start analysis in background
        logger.info(f"Starting analysis for file: {file_path} with analysis ID: {analysis_id}")
        background_tasks.add_task(analyze_contract_sync, file_path, analysis_id)
        
        return analysis_status[analysis_id]
        
    except Exception as e:
        logger.error(f"Error in analyze_contract: {str(e)}")
        analysis_status[analysis_id].status = "failed"
        analysis_status[analysis_id].progress = 0
        analysis_status[analysis_id].message = f"Analysis failed: {str(e)}"
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/api/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(analysis_id: str):
    """Get the result of a completed analysis"""
    result_path = os.path.join(settings.results_folder, f"{analysis_id}.json")
    
    # First check the analysis status
    status = analysis_status.get(analysis_id)
    
    # If we have status in memory
    if status:
        if status.status == "processing" or status.status == "queued":
            # Analysis is still in progress, return status with 202 code
            logger.info(f"Analysis {analysis_id} still in progress: {status.status}, progress: {status.progress}")
            return JSONResponse(
                status_code=202,
                content=status.dict()
            )
        elif status.status == "failed":
            # Analysis failed
            logger.error(f"Analysis {analysis_id} failed: {status.message}")
            raise HTTPException(status_code=500, detail=status.message)
    
    # If file doesn't exist
    if not os.path.exists(result_path):
        logger.error(f"Analysis result file not found: {result_path}")
        raise HTTPException(status_code=404, detail=f"Analysis result not found for ID {analysis_id}")
    
    try:
        # Try to load the result file with improved handling
        logger.info(f"Attempting to load analysis result for {analysis_id} from {result_path}")
        result = load_analysis_results(result_path)
        logger.info(f"Successfully loaded results for analysis {analysis_id}")
        return result
    except FileNotFoundError:
        logger.error(f"Analysis result file disappeared: {result_path}")
        raise HTTPException(status_code=404, detail="Analysis result file disappeared")
    except PermissionError as pe:
        logger.error(f"Permission error reading analysis result: {str(pe)}")
        # Check if it might be a file locking issue
        import time
        time.sleep(0.5)  # Wait a moment
        try:
            # Try one more time after a short delay
            result = load_analysis_results(result_path)
            return result
        except Exception as retry_error:
            raise HTTPException(status_code=500, detail=f"Permission error accessing result file: {str(retry_error)}")
    except Exception as e:
        logger.error(f"Error loading analysis result for {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading analysis result: {str(e)}")

@app.get("/api/analysis/{analysis_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """Get the status of an analysis"""
    status = analysis_status.get(analysis_id)
    if not status:
        # Check if result exists
        result_path = os.path.join(settings.results_folder, f"{analysis_id}.json")
        if os.path.exists(result_path):
            return AnalysisStatus(
                id=analysis_id,
                status="completed",
                progress=100,
                message="Analysis completed"
            )
        raise HTTPException(status_code=404, detail="Analysis not found")
    return status

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Add startup event to create necessary directories
@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup"""
    os.makedirs(settings.upload_folder, exist_ok=True)
    os.makedirs(settings.results_folder, exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
