"""
Event Emitter for Smart Contract Analysis Service
This module provides functionality to emit real-time WebSocket events during analysis.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from websocket import manager
from websocket.events import (
    EventType,
    analysis_progress_event,
    analysis_complete_event,
    analysis_error_event,
    vulnerability_detected_event,
    VulnerabilityData
)

logger = logging.getLogger(__name__)

class AnalysisEventEmitter:
    """
    Event emitter for the analysis service that handles WebSocket events
    """
    
    @staticmethod
    async def emit_progress(
        analysis_id: str, 
        percent: float, 
        step: str, 
        details: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Emit a progress update event
        
        Args:
            analysis_id: The ID of the analysis
            percent: Progress percentage (0.0 to 1.0)
            step: Current step description
            details: Optional details about the current step
            user_id: Optional user ID to send the event to (if None, broadcast)
        """
        progress_data = {
            "percent": percent,
            "step": step,
            "details": details
        }
        
        event = analysis_progress_event(analysis_id, progress_data)
        
        try:
            if user_id:
                await manager.send_to_user(user_id, event)
            else:
                await manager.broadcast(event)
                
            logger.debug(f"Emitted progress event for analysis {analysis_id}: {percent:.0%} - {step}")
        except Exception as e:
            logger.error(f"Failed to emit progress event: {str(e)}")
    
    @staticmethod
    async def emit_vulnerability_detected(
        analysis_id: str,
        vuln_type: str,
        severity: str,
        description: str,
        file_name: str,
        line_number: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Emit a vulnerability detected event
        
        Args:
            analysis_id: The ID of the analysis
            vuln_type: Type of vulnerability
            severity: Severity level (critical, high, medium, low)
            description: Description of the vulnerability
            file_name: Name of the file containing the vulnerability
            line_number: Optional line number where vulnerability was found
            user_id: Optional user ID to send the event to (if None, broadcast)
        """
        vulnerability = VulnerabilityData(
            type=vuln_type,
            severity=severity,
            description=description,
            file_name=file_name,
            line_number=line_number
        )
        
        event = vulnerability_detected_event(analysis_id, vulnerability)
        
        try:
            if user_id:
                await manager.send_to_user(user_id, event)
            else:
                await manager.broadcast(event)
                
            logger.debug(f"Emitted vulnerability event for analysis {analysis_id}: {vuln_type} ({severity})")
        except Exception as e:
            logger.error(f"Failed to emit vulnerability event: {str(e)}")
    
    @staticmethod
    async def emit_analysis_complete(
        analysis_id: str,
        contract_name: str,
        file_count: int,
        results_summary: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        Emit an analysis complete event
        
        Args:
            analysis_id: The ID of the analysis
            contract_name: Name of the analyzed contract
            file_count: Number of files analyzed
            results_summary: Summary of analysis results
            user_id: Optional user ID to send the event to (if None, broadcast)
        """
        analysis_data = {
            "analysis_id": analysis_id,
            "contract_name": contract_name,
            "file_count": file_count,
            "status": "completed"
        }
        
        event = analysis_complete_event(analysis_data, results_summary)
        
        try:
            if user_id:
                await manager.send_to_user(user_id, event)
            else:
                await manager.broadcast(event)
                
            logger.info(f"Emitted completion event for analysis {analysis_id}")
        except Exception as e:
            logger.error(f"Failed to emit completion event: {str(e)}")
    
    @staticmethod
    async def emit_analysis_error(
        analysis_id: str,
        error: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Emit an analysis error event
        
        Args:
            analysis_id: The ID of the analysis
            error: Error message
            user_id: Optional user ID to send the event to (if None, broadcast)
        """
        event = analysis_error_event(analysis_id, error)
        
        try:
            if user_id:
                await manager.send_to_user(user_id, event)
            else:
                await manager.broadcast(event)
                
            logger.error(f"Emitted error event for analysis {analysis_id}: {error}")
        except Exception as e:
            logger.error(f"Failed to emit error event: {str(e)}")

# Create singleton instance
event_emitter = AnalysisEventEmitter()
