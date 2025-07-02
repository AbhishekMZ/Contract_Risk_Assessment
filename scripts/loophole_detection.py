# loophole_detection.py
import os
import subprocess
import json
import re
import sys
import argparse
from glob import glob

PREPROCESSED_DIR = "Preprocessed_Contracts"
DETECTION_DIR = "Detection_Results"
METADATA_FILE = os.path.join(PREPROCESSED_DIR, "metadata.json")
EXTERNAL_DIR = "External_Contracts"
EXTERNAL_RESULTS_DIR = os.path.join("External_Results", "detections")
EXTERNAL_FEATURES_DIR = os.path.join("External_Results", "features")
MODELS_DIR = "Models"

# ... (CUSTOM_RULES are fine) ...
CUSTOM_RULES = [
    {
        "name": "Timestamp_Dependency",
        "pattern": r"block\.timestamp",
        "description": "Use of block.timestamp, can be manipulated by miners.",
        "severity": "Medium"
    },
    {
        "name": "TX_Origin_Usage",
        "pattern": r"tx\.origin",
        "description": "Use of tx.origin for authentication, vulnerable to phishing.",
        "severity": "High"
    },
    {
        "name": "Integer_Overflow_Underflow_Candidate_Basic",
        "pattern": r"\w+\s*(\+\+|--|\+=|-=|\*=|/=)\s*\w+",
        "description": "Potential basic integer arithmetic operation, needs careful review for overflow/underflow. Slither is much better at this.",
        "severity": "Low"
    },
    {
        "name": "Low_Level_Call",
        "pattern": r"\.(call|delegatecall|staticcall)\s*\(",
        "description": "Use of low-level calls (.call, .delegatecall, .staticcall), requires careful handling of return values and gas.",
        "severity": "Medium"
    }
]

def run_slither_analysis(filepath):
    contract_name = os.path.basename(filepath)
    print(f"  Analyzing {contract_name} with Slither...")

    output_json_path = os.path.join(DETECTION_DIR, f"{os.path.splitext(contract_name)[0]}_slither_report.json")

    # *********************************************************************
    # Specify the solc version or use solc-select for Slither CLI
    # This should match the version used/needed for feature_extraction.py
    # For contracts using 'constant' on functions, try '0.4.24' or '0.4.26'
    SOLC_VERSION_OR_SELECT = "0.4.24"  # Example: A specific version
    # If you ran `solc-select use 0.4.24` before the script, Slither might pick it up.
    # To be explicit with solc-select:
    # USE_SOLC_SELECT = True
    # SOLC_VERSION_FOR_SELECT = "0.4.24"
    # *********************************************************************

    cmd = [
        "slither", filepath,
        "--json", output_json_path,
        "--disable-color"
    ]

    # Add the solc version argument
    # Option A: Using --solc with a path (if you know the exact path to solc 0.4.24)
    # Example: cmd.extend(["--solc", "/path/to/your/solc-0.4.24"])
    # Option B: Using --solc-solcs-select (if solc-select is set up and Slither version supports it)
    # This tells Slither to ask solc-select for the compiler
    cmd.extend(["--solc-solcs-select", SOLC_VERSION_OR_SELECT])
    # Option C: Using --solc with just the version string (Slither will try to find it)
    # This is often less reliable than solc-select if you have many versions.
    # cmd.extend(["--solc", SOLC_VERSION_OR_SELECT])


    # Add --solc-ast if you want Slither to use the AST from solc directly, might help with complex projects
    # cmd.extend(["--solc-args", "--allow-paths .,node_modules"]) # Example if you have imports

    try:
        # Ensure DETECTION_DIR exists for Slither to write its JSON output
        if not os.path.exists(os.path.dirname(output_json_path)):
            os.makedirs(os.path.dirname(output_json_path))

        print(f"    Running Slither command: {' '.join(cmd)}") # For debugging
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if os.path.exists(output_json_path) and os.path.getsize(output_json_path) > 0:
            with open(output_json_path, 'r', encoding='utf-8') as f:
                try:
                    slither_data = json.load(f)
                    if result.stderr and not slither_data.get("success", True):
                        slither_data["slither_stderr"] = result.stderr.strip()
                    return slither_data
                except json.JSONDecodeError:
                    print(f"    Error: Slither produced an invalid JSON for {contract_name}.")
                    # ... (rest of error handling for invalid JSON) ...
                    error_content = ""
                    try:
                        with open(output_json_path, 'r', encoding='utf-8', errors='ignore') as f_err_read:
                            error_content = f_err_read.read()
                    except Exception:
                        pass 
                    return {"results": {"detectors": []}, "success": False, "error": "Invalid JSON output from Slither", "raw_output": error_content, "slither_stderr": result.stderr.strip()}
        else:
            print(f"    Error: Slither did not produce an output JSON for {contract_name} at {output_json_path}.")
            if result.stdout: print(f"    Slither stdout: {result.stdout[:500]}")
            if result.stderr: print(f"    Slither stderr: {result.stderr[:500]}") # This is important for debugging
            return {"results": {"detectors": []}, "success": False, "error": "Slither failed to produce output JSON.", "details": result.stderr.strip()}

    except FileNotFoundError:
        # ... (rest of FileNotFoundError handling) ...
        print("CRITICAL Error: Slither command not found. Is Slither installed and in PATH?")
        return {"results": {"detectors": []}, "success": False, "error": "Slither not found"}
    except Exception as e:
        # ... (rest of general Exception handling) ...
        print(f"  Exception running Slither on {filepath}: {e}")
        return {"results": {"detectors": []}, "success": False, "error": str(e)}

# ... (apply_custom_rules and detect_loopholes functions remain largely the same as before) ...
# Make sure detect_loopholes calls the updated run_slither_analysis

def apply_custom_rules(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        for line_num, line in enumerate(content.splitlines(), 1):
            for rule in CUSTOM_RULES:
                if re.search(rule["pattern"], line, re.IGNORECASE):
                    findings.append({
                        "check": rule["name"],
                        "impact": rule["severity"],
                        "confidence": "Medium",
                        "description": f"{rule['description']} (Custom Rule Match)",
                        "elements": [{
                            "type": "line",
                            "name": line.strip(),
                            "source_mapping": {
                                "start": -1, "length": -1,
                                "lines": [line_num],
                                "filename_relative": os.path.basename(filepath)
                            }
                        }]
                    })
    except Exception as e:
        print(f"  Error applying custom rules to {filepath}: {e}")
    return findings

def detect_loopholes():
    if not os.path.exists(PREPROCESSED_DIR):
        print(f"Error: Preprocessed directory '{os.path.abspath(PREPROCESSED_DIR)}' not found.")
        sys.exit(1)

    if not os.path.exists(METADATA_FILE):
        print(f"Error: Metadata file '{os.path.abspath(METADATA_FILE)}' not found. Run preprocessing first.")
        sys.exit(1)

    if not os.path.exists(DETECTION_DIR):
        os.makedirs(DETECTION_DIR)

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"Starting loophole detection from '{PREPROCESSED_DIR}'...")

    all_detection_results = {}
    successful_analyses = 0
    failed_slither_runs = 0

    for contract_filename_key, meta_info in metadata.items():
        processed_filepath = meta_info.get("processed_filepath")
        if not processed_filepath or not os.path.exists(processed_filepath):
            print(f"Skipping {contract_filename_key}: processed file path '{processed_filepath}' not found or invalid.")
            failed_slither_runs +=1
            error_report = {
                "slither_success": False,
                "slither_error": "Processed file not found.",
                "slither_findings": [],
                "custom_findings": [],
                "total_slither_issues": 0,
                "total_custom_issues": 0
            }
            result_filename = f"{os.path.splitext(contract_filename_key)[0]}_detection_report.json"
            result_filepath = os.path.join(DETECTION_DIR, result_filename)
            with open(result_filepath, 'w', encoding='utf-8') as f_res:
                json.dump(error_report, f_res, indent=4)
            all_detection_results[contract_filename_key] = result_filepath
            continue

        print(f"Processing {processed_filepath}...")

        slither_raw_output = run_slither_analysis(processed_filepath) # This now uses the modified cmd

        slither_findings = []
        slither_success = slither_raw_output.get("success", False)
        slither_error_msg = slither_raw_output.get("error")

        if slither_raw_output and "results" in slither_raw_output and "detectors" in slither_raw_output["results"]:
            slither_findings = slither_raw_output["results"]["detectors"]
            if slither_success:
                successful_analyses +=1
            else:
                print(f"    Slither analysis for {contract_filename_key} reported success=false but provided findings (e.g., compilation errors listed as issues).")
                successful_analyses +=1
        else:
            print(f"    Slither analysis failed or produced no detector results for {contract_filename_key}. Error: {slither_error_msg or 'Unknown Slither issue'}")
            failed_slither_runs +=1

        custom_findings = apply_custom_rules(processed_filepath)

        combined_results = {
            "slither_success": slither_success,
            "slither_error": slither_error_msg,
            "slither_stderr": slither_raw_output.get("slither_stderr"),
            "slither_findings": slither_findings,
            "custom_findings": custom_findings,
            "total_slither_issues": len(slither_findings),
            "total_custom_issues": len(custom_findings)
        }

        result_filename = f"{os.path.splitext(contract_filename_key)[0]}_detection_report.json"
        result_filepath = os.path.join(DETECTION_DIR, result_filename)
        with open(result_filepath, 'w', encoding='utf-8') as f_res:
            json.dump(combined_results, f_res, indent=4)

        all_detection_results[contract_filename_key] = result_filepath
        print(f"  Detection report saved to {result_filepath}")

    manifest_path = os.path.join(DETECTION_DIR, "detection_manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f_manifest:
        json.dump(all_detection_results, f_manifest, indent=4)

    print("\n--- Loophole Detection Summary ---")
    print(f"Contracts for which Slither produced a parsable report: {successful_analyses}")
    print(f"Contracts where Slither run failed or produced unusable output: {failed_slither_runs}")
    print(f"Detection reports and manifest saved in '{DETECTION_DIR}'")


def detect_external_loopholes(contract_path=None):
            """Detect loopholes in external contracts using trained model and Slither"""
            os.makedirs(EXTERNAL_RESULTS_DIR, exist_ok=True)
            
            if contract_path:
                # Process a specific external contract
                contracts = [contract_path]
            else:
                # Process all contracts in the external directory
                contracts = glob(os.path.join(EXTERNAL_DIR, '*.sol'))
            
            if not contracts:
                print(f"No external contracts found in {EXTERNAL_DIR}/")
                return
            
            # Load the trained model if it exists
            model_path = os.path.join(MODELS_DIR, 'vulnerability_patterns.json')
            model_patterns = None
            if os.path.exists(model_path):
                try:
                    with open(model_path, 'r', encoding='utf-8') as f:
                        model_patterns = json.load(f)
                    print(f"Loaded vulnerability model with {len(model_patterns.get('vulnerability_types', {}))} patterns")
                except Exception as e:
                    print(f"Error loading model: {e}")
                    model_patterns = None
            else:
                print("No trained model found. Running detection with standard rules only.")
            
            print(f"Detecting loopholes in {len(contracts)} external contract(s)...")
            
            for contract_file in contracts:
                contract_name = os.path.basename(contract_file)
                print(f"Processing external contract: {contract_name}")
                
                # Run Slither analysis
                slither_raw_output = run_slither_analysis(contract_file)
                
                slither_findings = []
                slither_success = slither_raw_output.get("success", False)
                
                if slither_raw_output and "results" in slither_raw_output and "detectors" in slither_raw_output["results"]:
                    slither_findings = slither_raw_output["results"]["detectors"]
                
                # Apply custom rules
                custom_findings = apply_custom_rules(contract_file)
                
                # Apply model-based detection if model is available
                model_findings = []
                if model_patterns:
                    try:
                        with open(contract_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for known vulnerability patterns from the model
                        for vuln_type, patterns in model_patterns.get('code_patterns', {}).items():
                            for line_num, line in enumerate(content.splitlines(), 1):
                                for pattern in patterns:
                                    # Create a simple pattern from the code line by keeping core parts
                                    core_pattern = re.sub(r'\s+', '\\s+', re.escape(pattern))
                                    core_pattern = re.sub(r'\\\w+\\s+\\\w+', '\\w+\\s+\\w+', core_pattern) # Replace variable names
                                    
                                    if re.search(core_pattern, line, re.IGNORECASE):
                                        severity = model_patterns.get('vulnerability_types', {}).get(vuln_type, {}).get('severity', 'Medium')
                                        model_findings.append({
                                            "check": f"Model_{vuln_type}",
                                            "impact": severity,
                                            "confidence": "Medium",
                                            "description": f"Potential {vuln_type} vulnerability detected based on trained model patterns",
                                            "elements": [{
                                                "type": "line",
                                                "name": line.strip(),
                                                "source_mapping": {
                                                    "start": -1, "length": -1,
                                                    "lines": [line_num],
                                                    "filename_relative": contract_name
                                                }
                                            }]
                                        })
                    except Exception as e:
                        print(f"Error applying model-based detection: {e}")
                
                # Combine all findings
                all_findings = {
                    "contract_file": contract_name,
                    "slither_success": slither_success,
                    "slither_findings": slither_findings,
                    "custom_findings": custom_findings,
                    "model_findings": model_findings,
                    "total_slither_issues": len(slither_findings),
                    "total_custom_issues": len(custom_findings),
                    "total_model_issues": len(model_findings)
                }
                
                # Save results
                # Use the filename pattern expected by generate_report.py
                result_filename = f"{os.path.splitext(contract_name)[0]}_detection.json"
                result_filepath = os.path.join(EXTERNAL_RESULTS_DIR, result_filename)
                with open(result_filepath, 'w', encoding='utf-8') as f_res:
                    json.dump(all_findings, f_res, indent=4)
                    
                print(f"  Detection complete. Found {len(slither_findings)} Slither issues, {len(custom_findings)} custom rule issues, and {len(model_findings)} model-based issues.")
                print(f"  Results saved to {result_filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Detect loopholes in smart contracts')
    parser.add_argument('--external', action='store_true', help='Detect loopholes in external contracts')
    parser.add_argument('--contract', type=str, help='Path to a specific external contract')
    
    args = parser.parse_args()
    
    # Check for Slither before starting
    try:
        subprocess.run(["slither", "--version"], capture_output=True, check=True)
        
        if args.external:
            detect_external_loopholes()
        elif args.contract:
            detect_external_loopholes(args.contract)
        else:
            detect_loopholes()
            
    except FileNotFoundError:
        print("CRITICAL: The 'slither' command could not be found.")
        print("Please ensure 'slither-analyzer' is correctly installed and in your PATH.")
        print("Try: pip install slither-analyzer")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("CRITICAL: The 'slither' command is available but returned an error when checking its version.")
        print("This could indicate a problem with the Slither installation.")
        sys.exit(1)