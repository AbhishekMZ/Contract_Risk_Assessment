"""
Utility functions for contract analysis.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_analysis_results(
    results: Dict[str, Any], 
    output_path: str
) -> str:
    """Save analysis results to a JSON file.
    
    Args:
        results: The analysis results to save
        output_path: Full path to the output file
        
    Returns:
        The path to the saved file
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to a temporary file first
    temp_path = f"{output_path}.tmp"
    
    try:
        # Write to the temp file
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            # Ensure flush to disk
            f.flush()
            os.fsync(f.fileno())
        
        # If on Windows, ensure the file handle is fully closed before renaming
        import time
        time.sleep(0.2)
        
        # Try atomic rename
        try:
            import shutil
            shutil.move(temp_path, output_path)
        except Exception:
            # If atomic rename fails, try direct copy and remove
            with open(temp_path, 'r', encoding='utf-8') as src:
                with open(output_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                    dst.flush()
                    os.fsync(dst.fileno())
            # Try to remove the temp file, ignore if it fails
            try:
                os.remove(temp_path)
            except Exception:
                pass
    except Exception as e:
        # If anything goes wrong, clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        raise e
    
    return output_path


def load_analysis_results(file_path: str) -> Dict[str, Any]:
    """Load analysis results from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        The loaded JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be accessed
        json.JSONDecodeError: If the file contains invalid JSON
    """
    # Maximum number of attempts to read the file
    max_attempts = 3
    backoff_delay = 0.5  # Start with 0.5 seconds
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Analysis result file not found: {file_path}")
    
    # Check file size
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"Analysis result file is empty: {file_path}")
    
    last_error = None
    import time
    
    # Try multiple times with backoff
    for attempt in range(max_attempts):
        try:
            # Use binary mode and decode manually to avoid encoding issues
            with open(file_path, 'rb') as f:
                data = f.read()
                return json.loads(data.decode('utf-8'))
        except (PermissionError, OSError) as e:
            # If permission error or file locked, wait and retry
            last_error = e
            time.sleep(backoff_delay)
            backoff_delay *= 2  # Exponential backoff
        except json.JSONDecodeError as e:
            # Don't retry for JSON decode errors
            raise ValueError(f"Invalid JSON in analysis result file: {e}")
    
    # If we got here, all attempts failed
    if last_error:
        raise type(last_error)(f"Failed to read analysis result after {max_attempts} attempts: {last_error}")
    else:
        raise OSError(f"Failed to read analysis result file: {file_path}")


def format_severity(severity: str) -> str:
    """Format severity level with color coding."""
    severity = severity.lower()
    if severity == 'high':
        return '🔴 HIGH'
    elif severity == 'medium':
        return '🟠 MEDIUM'
    elif severity == 'low':
        return '🟡 LOW'
    elif severity == 'info':
        return '🔵 INFO'
    return severity

def get_contract_name(file_path: str) -> str:
    """Extract contract name from file path."""
    return Path(file_path).stem


def count_vulnerabilities_by_severity(
    findings: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Count vulnerabilities by severity level."""
    counts = {
        'high': 0,
        'medium': 0,
        'low': 0,
        'info': 0,
        'total': len(findings)
    }
    
    for finding in findings:
        severity = finding.get('severity', 'info').lower()
        if severity in counts:
            counts[severity] += 1
    
    return counts
