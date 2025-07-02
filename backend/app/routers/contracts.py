import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.session import get_db
from ..models.contract import Contract, Analysis, ContractStatus, SeverityLevel
from ..models.user import User
from ..schemas.contract import ContractCreate, ContractInDB, AnalysisCreate, AnalysisInDB
from ..core.security import get_current_user
from ..core.config import settings

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload/", response_model=ContractInDB)
async def upload_contract(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Upload a smart contract for analysis."""
    # Validate file type
    if not file.filename or not file.filename.endswith('.sol'):
        raise HTTPException(
            status_code=400,
            detail="Only .sol files are supported"
        )
    
    # Save file
    timestamp = int(datetime.utcnow().timestamp())
    filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Create contract record
    contract = Contract(
        name=file.filename,
        file_path=str(file_path),
        original_filename=file.filename,
        file_size=os.path.getsize(file_path),
        file_type=file.content_type or "application/octet-stream",
        status=ContractStatus.UPLOADED,
        owner_id=current_user.id,
    )
    
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    
    return contract

@router.get("/", response_model=List[ContractInDB])
async def list_contracts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all contracts for the current user."""
    result = await db.execute(
        select(Contract)
        .filter(Contract.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{contract_id}", response_model=ContractInDB)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a specific contract by ID."""
    result = await db.execute(
        select(Contract)
        .filter(Contract.id == contract_id, Contract.owner_id == current_user.id)
    )
    contract = result.scalars().first()
    
    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )
    
    return contract

@router.post("/{contract_id}/analyze", response_model=AnalysisInDB)
async def analyze_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Analyze a contract."""
    # Get contract
    result = await db.execute(
        select(Contract)
        .filter(Contract.id == contract_id, Contract.owner_id == current_user.id)
    )
    contract = result.scalars().first()
    
    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )
    
    # Update contract status
    contract.status = ContractStatus.ANALYZING
    await db.commit()
    
    try:
        # TODO: Implement actual contract analysis here
        # This is a placeholder for the analysis logic
        analysis_result = {
            "issues": [
                {
                    "severity": "high",
                    "description": "Reentrancy vulnerability detected",
                    "line": 42,
                    "pattern": "call.value()()",
                    "recommendation": "Use Checks-Effects-Interactions pattern"
                },
                {
                    "severity": "medium",
                    "description": "Unchecked external call",
                    "line": 128,
                    "pattern": "address.call()",
                    "recommendation": "Validate return values of external calls"
                }
            ]
        }
        
        # Create analysis record
        analysis = Analysis(
            contract_id=contract.id,
            user_id=current_user.id,
            analyzer_version="1.0.0",
            analysis_time_ms=500,  # Example value
            findings=analysis_result["issues"],
            summary={
                "total_issues": len(analysis_result["issues"]),
                "high_issues": len([i for i in analysis_result["issues"] if i["severity"] == "high"]),
                "medium_issues": len([i for i in analysis_result["issues"] if i["severity"] == "medium"]),
                "low_issues": len([i for i in analysis_result["issues"] if i["severity"] == "low"])
            }
        )
        
        db.add(analysis)
        contract.status = ContractStatus.COMPLETED
        await db.commit()
        await db.refresh(analysis)
        
        return analysis
        
    except Exception as e:
        contract.status = ContractStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/{contract_id}/analyses", response_model=List[AnalysisInDB])
async def list_analyses(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all analyses for a contract."""
    # Verify contract ownership
    result = await db.execute(
        select(Contract)
        .filter(Contract.id == contract_id, Contract.owner_id == current_user.id)
    )
    if not result.scalars().first():
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )
    
    # Get analyses
    result = await db.execute(
        select(Analysis)
        .filter(Analysis.contract_id == contract_id)
        .order_by(Analysis.created_at.desc())
    )
    
    return result.scalars().all()
