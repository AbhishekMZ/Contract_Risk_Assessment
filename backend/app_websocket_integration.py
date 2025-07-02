"""
This module demonstrates how to integrate WebSockets into the main FastAPI application.
Add these changes to your main app.py file.
"""

# Import the WebSocket router and necessary dependencies
from fastapi import FastAPI, Depends
from websocket.router import include_websocket_routes
from websocket import manager, EventType
from websocket.events import create_event, analysis_progress_event, analysis_complete_event
import asyncio

# Sample code to integrate WebSockets with your existing FastAPI app
# Replace this with your actual app initialization
app = FastAPI(title="Smart Contract Analyzer API")

# Include the WebSocket routes
include_websocket_routes(app)

# Example of how to send updates from your analysis service
async def send_analysis_updates(analysis_id: str, user_id: str = None):
    """
    Example function demonstrating how to send real-time updates during analysis
    This would be called from your analysis service
    """
    # Example: Send initial progress update
    progress_data = {
        "analysis_id": analysis_id,
        "percent": 0.0,
        "step": "Starting analysis",
        "details": "Initializing Solidity compiler"
    }
    
    # If we have a user_id, send to that user's connections
    if user_id:
        await manager.send_to_user(user_id, analysis_progress_event(
            analysis_id=analysis_id,
            progress=progress_data
        ))
    else:
        # Otherwise broadcast (useful for admin dashboards)
        await manager.broadcast(analysis_progress_event(
            analysis_id=analysis_id,
            progress=progress_data
        ))
    
    # Simulate analysis process with updates
    for i in range(1, 5):
        # In a real implementation, this would be actual analysis progress
        await asyncio.sleep(1)  # Simulate processing time
        
        steps = [
            "Parsing Solidity code",
            "Running static analysis",
            "Executing pattern matching",
            "Generating vulnerability report"
        ]
        
        progress_data = {
            "analysis_id": analysis_id,
            "percent": i * 0.25,
            "step": steps[i-1],
            "details": f"Processing step {i}/4"
        }
        
        # Send update
        if user_id:
            await manager.send_to_user(user_id, analysis_progress_event(
                analysis_id=analysis_id,
                progress_data=progress_data
            ))
        else:
            await manager.broadcast(analysis_progress_event(
                analysis_id=analysis_id,
                progress_data=progress_data
            ))
    
    # Send completion notification
    completion_data = {
        "analysis_id": analysis_id,
        "status": "completed",
        "contract_name": "ExampleContract",
        "file_count": 1,
        "results_summary": {
            "vulnerability_count": 3,
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 0
        }
    }
    
    if user_id:
        await manager.send_to_user(user_id, analysis_complete_event(
            analysis_id=analysis_id,
            analysis_data=completion_data
        ))
    else:
        await manager.broadcast(analysis_complete_event(
            analysis_id=analysis_id,
            analysis_data=completion_data
        ))


# Example of how to integrate with your analysis endpoint
@app.post("/contracts/analyze")
async def analyze_contract(contract_data: dict, user_id: str = None):
    """
    Example endpoint for contract analysis that uses WebSockets for progress updates
    """
    # Create a unique analysis ID
    from uuid import uuid4
    analysis_id = str(uuid4())
    
    # Start analysis in background task
    import asyncio
    asyncio.create_task(send_analysis_updates(analysis_id, user_id))
    
    # Return initial response
    return {
        "analysis_id": analysis_id,
        "status": "processing",
        "message": "Analysis started. Connect to WebSocket for real-time updates."
    }


"""
Usage instructions:

1. Add the WebSocket integration to your main FastAPI app:
   - Import the WebSocket router and manager
   - Call include_websocket_routes(app)

2. To send real-time updates from your analysis service:
   - Import the manager and event helper functions
   - Call appropriate event creation functions and send via manager
   
3. Modify your analysis endpoints to start background tasks that send updates
"""
