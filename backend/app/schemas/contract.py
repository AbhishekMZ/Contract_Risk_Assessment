from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class ContractStatus(str, Enum):
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class FindingBase(BaseModel):
    severity: SeverityLevel
    description: str
    line: Optional[int] = None
    pattern: Optional[str] = None
    recommendation: Optional[str] = None

class AnalysisBase(BaseModel):
    analyzer_version: str
    analysis_time_ms: Optional[int] = None

class AnalysisCreate(AnalysisBase):
    contract_id: int

class AnalysisInDB(AnalysisBase):
    id: int
    contract_id: int
    user_id: int
    findings: List[Dict[str, Any]]
    summary: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ContractBase(BaseModel):
    name: str
    description: Optional[str] = None

class ContractCreate(ContractBase):
    pass

class ContractInDB(ContractBase):
    id: int
    owner_id: int
    file_path: str
    original_filename: str
    file_size: int
    file_type: str
    status: ContractStatus
    created_at: datetime
    updated_at: datetime
    analyses: List[AnalysisInDB] = []

    class Config:
        orm_mode = True

class AnalysisWithContract(AnalysisInDB):
    contract: ContractInDB
