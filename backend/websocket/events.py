from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class EventType(str, Enum):
    """
    Types of WebSocket events for the Smart Contract Analyzer
    """
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress" 
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_ERROR = "analysis_error"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    CONNECTION_ESTABLISHED = "connection_established"
    BATCH_PROGRESS = "batch_progress"
    SYSTEM_NOTIFICATION = "system_notification"


class ProgressData(BaseModel):
    """
    Data model for progress updates
    """
    percent: float
    step: str
    details: Optional[str] = None
    

class VulnerabilityData(BaseModel):
    """
    Data model for detected vulnerabilities
    """
    type: str
    severity: str
    line_number: Optional[int] = None
    description: str
    file_name: str


class AnalysisData(BaseModel):
    """
    Data model for analysis metadata
    """
    analysis_id: str
    contract_name: str
    file_count: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str


class BatchData(BaseModel):
    """
    Data model for batch processing updates
    """
    batch_id: str
    total_contracts: int
    completed: int
    in_progress: int
    failed: int
    estimated_completion_time: Optional[str] = None


class WebSocketEvent(BaseModel):
    """
    Base model for all WebSocket events
    """
    event: EventType
    data: Dict[str, Any]
    timestamp: str


def create_event(event_type: EventType, data: Dict[str, Any]) -> Dict:
    """
    Create a formatted WebSocket event with timestamp
    """
    from datetime import datetime
    
    return {
        "event": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def analysis_started_event(analysis_data: AnalysisData) -> Dict:
    """
    Create an analysis started event
    """
    data = analysis_data if isinstance(analysis_data, dict) else analysis_data.model_dump()
    return create_event(
        EventType.ANALYSIS_STARTED,
        data
    )


def analysis_progress_event(analysis_id: str, progress: Dict | ProgressData) -> Dict:
    """
    Create a progress update event
    """
    progress_data = progress if isinstance(progress, dict) else progress.model_dump()
    return create_event(
        EventType.ANALYSIS_PROGRESS,
        {
            "analysis_id": analysis_id,
            **progress_data
        }
    )


def analysis_complete_event(analysis_data: Dict | AnalysisData, results_summary: Dict) -> Dict:
    """
    Create an analysis complete event
    """
    data = analysis_data if isinstance(analysis_data, dict) else analysis_data.model_dump()
    return create_event(
        EventType.ANALYSIS_COMPLETE,
        {
            **data,
            "results_summary": results_summary
        }
    )


def vulnerability_detected_event(analysis_id: str, vulnerability: Dict | VulnerabilityData) -> Dict:
    """
    Create a vulnerability detected event
    """
    vuln_data = vulnerability if isinstance(vulnerability, dict) else vulnerability.model_dump()
    return create_event(
        EventType.VULNERABILITY_DETECTED, 
        {
            "analysis_id": analysis_id,
            "vulnerability": vuln_data
        }
    )


def analysis_error_event(analysis_id: str, error: str) -> Dict:
    """
    Create an analysis error event
    """
    return create_event(
        EventType.ANALYSIS_ERROR,
        {
            "analysis_id": analysis_id,
            "error": error
        }
    )


def batch_progress_event(batch_data: BatchData) -> Dict:
    """
    Create a batch progress event
    """
    return create_event(
        EventType.BATCH_PROGRESS,
        batch_data.model_dump()
    )
