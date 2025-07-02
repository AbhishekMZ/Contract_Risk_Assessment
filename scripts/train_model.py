# train_model.py
"""
Script to extract vulnerability patterns from processed contracts and save as a model.
This creates a "model" file that contains statistics and patterns from detected loopholes,
including patterns from known vulnerable contracts in not-so-smart-contracts.
"""
import os
import json
import pandas as pd
from glob import glob
import re
from pathlib import Path

# Update paths to work with the new directory structure
PROJECT_ROOT = Path(__file__).parent.parent
DETECTION_DIR = PROJECT_ROOT / "data" / "Detection_Results"
MODELS_DIR = PROJECT_ROOT / "data" / "Models"

def extract_vulnerability_patterns():
    """
    Extract patterns from detection results and build a vulnerability model
    Includes both regular contract analysis and known vulnerable contracts
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, 'vulnerability_patterns.json')
    
    # Patterns dictionary to store vulnerability information
    patterns = {
        "metadata": {
            "version": "1.0",
            "creation_date": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_contracts_analyzed": 0,
            "vulnerable_contracts_analyzed": 0
        },
        "vulnerability_types": {},
        "code_patterns": {}
    }
    
    # Get all detection report files
    regular_detection_files = list(DETECTION_DIR.glob('*_detection_report.json'))
    vulnerable_detection_files = list(DETECTION_DIR.glob('vulnerable/**/*_detection_report.json'))
    
    detection_files = regular_detection_files + vulnerable_detection_files
    
    if not detection_files:
        print(f"No detection reports found in {DETECTION_DIR}")
        return
    
    print(f"Analyzing {len(detection_files)} detection reports for patterns...")
    
    contract_count = 0
    vulnerable_contract_count = 0
    vulnerability_counts = {}
    
    # Process each detection report
    for detection_file in detection_files:
        try:
            # Handle both string paths and Path objects
            detection_path = str(detection_file)
            
            with open(detection_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # Check if this is a vulnerable contract
            is_vulnerable = 'vulnerable' in detection_path
            
            contract_count += 1
            if is_vulnerable:
                vulnerable_contract_count += 1
            
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
    patterns['metadata']['vulnerable_contracts_analyzed'] = vulnerable_contract_count
    
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
    import sys
    import subprocess
    
    print("Starting model training pipeline...")
    
    # First process vulnerable contracts from not-so-smart-contracts
    print("\n1. Processing vulnerable contracts from not-so-smart-contracts")
    try:
        # Try to import and run directly
        from process_vulnerable_contracts import extract_contracts, run_detection_on_contracts, update_detection_manifest
        print("Directly processing vulnerable contracts...")
        contract_files = extract_contracts()
        run_detection_on_contracts(contract_files)
        update_detection_manifest()
    except ImportError:
        # Fall back to running as subprocess
        print("Running vulnerable contract processing as a subprocess...")
        script_path = os.path.join(os.path.dirname(__file__), "process_vulnerable_contracts.py")
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("Vulnerable contract processing completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error processing vulnerable contracts: {e}")
                print("Continuing with model training using available detection results...")
        else:
            print(f"Warning: Vulnerable contract processing script not found at {script_path}")
            print("Continuing with model training using available detection results...")
    
    # Now extract vulnerability patterns and train the model
    print("\n2. Extracting vulnerability patterns and training model")
    model_data = extract_vulnerability_patterns()
    
    # Print a summary of the trained model
    if model_data and 'vulnerability_types' in model_data:
        print(f"\nModel Training Summary:")
        print(f"Total contracts analyzed: {model_data['metadata'].get('total_contracts_analyzed', 0)}")
        print(f"Known vulnerable contracts: {model_data['metadata'].get('vulnerable_contracts_analyzed', 0)}")
        print(f"Vulnerability types detected: {len(model_data['vulnerability_types'])}")
        print(f"\nTop vulnerability types:")
        
        # Sort vulnerabilities by count and print top 5
        sorted_vulns = sorted(
            model_data['vulnerability_types'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for i, (vuln_type, data) in enumerate(sorted_vulns[:5], 1):
            print(f"{i}. {vuln_type} - Count: {data['count']}, Severity: {data['severity']}")
    
    print("\nModel training complete!")
    print(f"Model saved to {os.path.join(MODELS_DIR, 'vulnerability_patterns.json')}")
    
