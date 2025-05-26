# train_model.py
"""
Script to extract vulnerability patterns from processed contracts and save as a model.
This creates a "model" file that contains statistics and patterns from detected loopholes.
"""
import os
import json
import pandas as pd
from glob import glob
import re

DETECTION_DIR = "Detection_Results"
MODELS_DIR = "Models"

def extract_vulnerability_patterns():
    """
    Extract patterns from detection results and build a vulnerability model
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, 'vulnerability_patterns.json')
    
    # Patterns dictionary to store vulnerability information
    patterns = {
        "metadata": {
            "version": "1.0",
            "creation_date": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_contracts_analyzed": 0
        },
        "vulnerability_types": {},
        "code_patterns": {}
    }
    
    # Get all detection report files
    detection_files = glob(os.path.join(DETECTION_DIR, '*_detection_report.json'))
    if not detection_files:
        print(f"No detection reports found in {DETECTION_DIR}/")
        return
    
    print(f"Analyzing {len(detection_files)} detection reports for patterns...")
    
    contract_count = 0
    vulnerability_counts = {}
    
    # Process each detection report
    for detection_file in detection_files:
        try:
            with open(detection_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
                
            contract_count += 1
            
            # Process Slither findings
            for finding in report.get('slither_findings', []):
                vuln_type = finding.get('check', 'unknown')
                if vuln_type not in vulnerability_counts:
                    vulnerability_counts[vuln_type] = 0
                vulnerability_counts[vuln_type] += 1
                
                # Extract code patterns from the elements
                for element in finding.get('elements', []):
                    if element.get('type') == 'line':
                        code_line = element.get('name', '').strip()
                        if code_line and len(code_line) > 5:  # Minimum meaningful length
                            if vuln_type not in patterns['code_patterns']:
                                patterns['code_patterns'][vuln_type] = []
                            # Add the pattern if it's not already in the list
                            if code_line not in patterns['code_patterns'][vuln_type]:
                                patterns['code_patterns'][vuln_type].append(code_line)
            
            # Process custom rule findings
            for finding in report.get('custom_findings', []):
                vuln_type = finding.get('check', 'unknown')
                if vuln_type not in vulnerability_counts:
                    vulnerability_counts[vuln_type] = 0
                vulnerability_counts[vuln_type] += 1
                
                # Extract code patterns from the elements
                for element in finding.get('elements', []):
                    if element.get('type') == 'line':
                        code_line = element.get('name', '').strip()
                        if code_line and len(code_line) > 5:  # Minimum meaningful length
                            if vuln_type not in patterns['code_patterns']:
                                patterns['code_patterns'][vuln_type] = []
                            # Add the pattern if it's not already in the list
                            if code_line not in patterns['code_patterns'][vuln_type]:
                                patterns['code_patterns'][vuln_type].append(code_line)
                
        except Exception as e:
            print(f"Error processing {os.path.basename(detection_file)}: {e}")
    
    # Update metadata
    patterns['metadata']['total_contracts_analyzed'] = contract_count
    
    # Create vulnerability type statistics
    for vuln_type, count in vulnerability_counts.items():
        patterns['vulnerability_types'][vuln_type] = {
            'count': count,
            'frequency': count / contract_count if contract_count > 0 else 0,
            'severity': get_severity_for_vulnerability(vuln_type)
        }
    
    # Save the model
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, indent=2)
    
    print(f"Model trained successfully. Found {len(patterns['vulnerability_types'])} vulnerability types.")
    print(f"Model saved to {model_path}")
    
    return patterns

def get_severity_for_vulnerability(vuln_type):
    """Map vulnerability types to severity levels based on common knowledge"""
    severity_map = {
        'reentrancy': 'High',
        'reentrancy-eth': 'High',
        'reentrancy-no-eth': 'Medium',
        'unchecked-transfer': 'High',
        'unchecked-lowlevel': 'High',
        'unchecked-send': 'Medium',
        'tx-origin': 'High',
        'TX_Origin_Usage': 'High',
        'timestamp': 'Medium',
        'Timestamp_Dependency': 'Medium',
        'Integer_Overflow_Underflow_Candidate_Basic': 'Medium',
        'uninitialized-local': 'Medium',
        'uninitialized-storage': 'High',
        'unused-return': 'Medium',
        'incorrect-equality': 'Medium',
        'shadowing-state': 'Medium',
        'suicidal': 'High',
        'arbitrary-send': 'High',
        'locked-ether': 'Medium',
        'Low_Level_Call': 'Medium'
    }
    
    # Default to Medium if not found
    return severity_map.get(vuln_type.lower(), 'Medium')

if __name__ == "__main__":
    print("Starting model training...")
    extract_vulnerability_patterns()
