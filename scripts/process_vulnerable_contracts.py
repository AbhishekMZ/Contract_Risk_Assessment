"""
Process vulnerable contracts from the not-so-smart-contracts directory.
This script extracts smart contracts from the not-so-smart-contracts repository,
runs detection tools on them, and prepares them for model training.
"""
import os
import sys
import json
import shutil
from pathlib import Path
import subprocess
import re

# Define directories
PROJECT_ROOT = Path(__file__).parent.parent
VULN_CONTRACTS_DIR = PROJECT_ROOT / "not-so-smart-contracts"
TEMP_CONTRACTS_DIR = PROJECT_ROOT / "data" / "SmartContracts" / "vulnerable"
VULN_DETECTION_DIR = PROJECT_ROOT / "data" / "Detection_Results" / "vulnerable"

# Ensure necessary directories exist
os.makedirs(TEMP_CONTRACTS_DIR, exist_ok=True)
os.makedirs(VULN_DETECTION_DIR, exist_ok=True)

# Map of vulnerability categories to more standardized names
VULNERABILITY_MAP = {
    'bad_randomness': 'Random_Number_Generation',
    'denial_of_service': 'DOS_Vulnerability',
    'forced_ether_reception': 'Force_Ether_Reception',
    'honeypots': 'Honeypot_Contract',
    'incorrect_interface': 'Incorrect_Interface',
    'integer_overflow': 'Integer_Overflow_Underflow',
    'race_condition': 'Race_Condition',
    'reentrancy': 'Reentrancy',
    'unchecked_external_call': 'Unchecked_External_Call',
    'unprotected_function': 'Unprotected_Function',
    'variable shadowing': 'Variable_Shadowing',
    'wrong_constructor_name': 'Wrong_Constructor_Name'
}

def extract_contracts():
    """
    Extract contracts from the not-so-smart-contracts directory and organize them
    for processing. Returns a list of contract files with their vulnerability types.
    """
    contract_files = []
    print("Extracting vulnerable contracts...")
    
    # Process each vulnerability category directory
    for vuln_dir in VULN_CONTRACTS_DIR.iterdir():
        if not vuln_dir.is_dir() or vuln_dir.name.startswith('.'):
            continue
            
        vuln_type = vuln_dir.name
        std_vuln_name = VULNERABILITY_MAP.get(vuln_type, vuln_type)
        
        print(f"Processing {vuln_type} contracts...")
        
        # Create category directory in the temp contracts directory
        category_dir = TEMP_CONTRACTS_DIR / std_vuln_name
        os.makedirs(category_dir, exist_ok=True)
        
        # Find and copy all Solidity files
        for sol_file in vuln_dir.glob('**/*.sol'):
            if sol_file.is_file():
                # Create a unique name to avoid overwriting
                dest_name = f"{std_vuln_name}_{sol_file.stem}.sol"
                dest_path = category_dir / dest_name
                
                # Copy the file
                shutil.copy2(sol_file, dest_path)
                contract_files.append({
                    'file_path': str(dest_path),
                    'vulnerability_type': std_vuln_name,
                    'original_path': str(sol_file)
                })
                
                print(f"  Copied {sol_file.name} to {dest_path}")
    
    print(f"Extracted {len(contract_files)} vulnerable contracts")
    return contract_files

def run_detection_on_contracts(contract_files):
    """
    Run loophole detection on the extracted contracts and generate detection reports.
    """
    try:
        # Import the detection script
        sys.path.append(str(PROJECT_ROOT))
        from scripts.loophole_detection import detect_loopholes
        
        print("Running vulnerability detection on extracted contracts...")
        
        # For each contract, run detection and save a custom report
        for contract in contract_files:
            file_path = contract['file_path']
            vuln_type = contract['vulnerability_type']
            
            # Get filename for the detection report
            contract_filename = os.path.basename(file_path)
            report_name = f"vulnerable_{contract_filename.replace('.sol', '')}_detection_report.json"
            report_path = os.path.join(VULN_DETECTION_DIR, report_name)
            
            # Run detection tools if available
            try:
                # Try to use the existing detection function
                results = detect_loopholes(file_path)
                
                # Add our known vulnerability as a custom finding
                if 'custom_findings' not in results:
                    results['custom_findings'] = []
                    
                # Create a custom finding entry with the known vulnerability
                custom_finding = {
                    'check': vuln_type,
                    'impact': 'High',
                    'confidence': 'High',
                    'description': f"Known vulnerability: {vuln_type}",
                    'elements': [
                        {
                            'type': 'contract',
                            'name': os.path.basename(file_path),
                            'source_mapping': {
                                'filename': file_path,
                                'lines': [1, 999]  # Placeholder line range
                            }
                        }
                    ]
                }
                
                # Add our custom finding to the results
                results['custom_findings'].append(custom_finding)
                
                # Save the detection report
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                    
                print(f"  Created detection report for {contract_filename}")
                
            except Exception as e:
                print(f"  Error detecting vulnerabilities in {contract_filename}: {e}")
                # Create a minimal detection report with our known vulnerability
                minimal_report = {
                    'contract_file': file_path,
                    'slither_findings': [],
                    'custom_findings': [
                        {
                            'check': vuln_type,
                            'impact': 'High',
                            'confidence': 'High',
                            'description': f"Known vulnerability: {vuln_type}",
                            'elements': [
                                {
                                    'type': 'contract',
                                    'name': os.path.basename(file_path),
                                    'source_mapping': {
                                        'filename': file_path,
                                        'lines': [1, 999]  # Placeholder line range
                                    }
                                }
                            ]
                        }
                    ]
                }
                
                # Save the minimal detection report
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(minimal_report, f, indent=2)
                    
                print(f"  Created minimal detection report for {contract_filename}")
    
    except ImportError as e:
        print(f"Error importing loophole_detection module: {e}")
        print("Falling back to creating detection reports directly...")
        
        # Create detection reports directly without running detection tools
        for contract in contract_files:
            file_path = contract['file_path']
            vuln_type = contract['vulnerability_type']
            
            # Get filename for the detection report
            contract_filename = os.path.basename(file_path)
            report_name = f"vulnerable_{contract_filename.replace('.sol', '')}_detection_report.json"
            report_path = os.path.join(VULN_DETECTION_DIR, report_name)
            
            # Create a detection report with the known vulnerability
            detection_report = {
                'contract_file': file_path,
                'slither_findings': [],
                'custom_findings': [
                    {
                        'check': vuln_type,
                        'impact': 'High',
                        'confidence': 'High',
                        'description': f"Known vulnerability: {vuln_type}",
                        'elements': [
                            {
                                'type': 'contract',
                                'name': os.path.basename(file_path),
                                'source_mapping': {
                                    'filename': file_path,
                                    'lines': [1, 999]  # Placeholder line range
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Save the detection report
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(detection_report, f, indent=2)
                
            print(f"  Created detection report for {contract_filename}")

def update_detection_manifest():
    """
    Update the detection manifest to include the vulnerable contract detection reports.
    """
    manifest_path = os.path.join(PROJECT_ROOT, 'data', 'Detection_Results', 'detection_manifest.json')
    
    # Load existing manifest if it exists
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError:
                manifest = {}
    else:
        manifest = {}
    
    # Add vulnerable contract detection reports to the manifest
    for report_file in os.listdir(VULN_DETECTION_DIR):
        if report_file.endswith('_detection_report.json'):
            contract_name = report_file.replace('_detection_report.json', '.sol')
            if contract_name.startswith('vulnerable_'):
                contract_name = contract_name[len('vulnerable_'):]
                
            report_path = os.path.join(VULN_DETECTION_DIR, report_file)
            manifest[contract_name] = report_path
    
    # Save updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Updated detection manifest at {manifest_path}")

if __name__ == "__main__":
    print("Starting vulnerable contract processing...")
    
    # Extract contracts from the not-so-smart-contracts directory
    contract_files = extract_contracts()
    
    # Run detection on the extracted contracts
    run_detection_on_contracts(contract_files)
    
    # Update the detection manifest
    update_detection_manifest()
    
    print("Vulnerable contract processing complete.")
