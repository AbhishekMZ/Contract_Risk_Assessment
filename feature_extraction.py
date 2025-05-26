# feature_extraction.py
import os
import json
import sys
import subprocess # For the initial solc-select check
import argparse
from glob import glob

PREPROCESSED_DIR = "Preprocessed_Contracts"
FEATURES_DIR = "Extracted_Features"
EXTERNAL_DIR = "External_Contracts"
EXTERNAL_FEATURES_DIR = os.path.join("External_Results", "features")
METADATA_FILE = os.path.join(PREPROCESSED_DIR, "metadata.json")

# --- Configuration ---
# Define the Solidity compiler version to be used by Slither's Python API.
# This should be consistent with the version used in loophole_detection.py for Slither CLI.
# For contracts using 'constant' on functions (pre-0.5.0), '0.4.24' or '0.4.26' are common.
# Ensure this version is installed via `solc-select install <version>`
SOLC_VERSION_FOR_SLITHER_API = "0.4.24"  # <<< IMPORTANT: SET THIS TO YOUR REQUIRED SOLC VERSION

def extract_all_features():
    if not os.path.exists(PREPROCESSED_DIR):
        print(f"Error: Preprocessed directory '{os.path.abspath(PREPROCESSED_DIR)}' not found.")
        sys.exit(1)

    if not os.path.exists(METADATA_FILE):
        print(f"Error: Metadata file '{os.path.abspath(METADATA_FILE)}' not found. Run preprocessing first.")
        sys.exit(1)

    if not os.path.exists(FEATURES_DIR):
        os.makedirs(FEATURES_DIR)

    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file '{METADATA_FILE}' not found. Ensure preprocessing ran successfully.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Metadata file '{METADATA_FILE}' is corrupted or not valid JSON.")
        sys.exit(1)


    print(f"Starting feature extraction from '{PREPROCESSED_DIR}'...")
    print(f"Attempting to use SOLC version via solc-select for Slither API: {SOLC_VERSION_FOR_SLITHER_API}")

    # --- Optional: Attempt to set solc-select version for the environment ---
    # This is a best-effort attempt; `solc_solcs_select` in Slither() is more direct.
    try:
        # This command tries to make solc-select switch the active 'solc' symlink/shim.
        # Slither might then pick this up if it just calls 'solc'.
        subprocess.run(["solc-select", "use", SOLC_VERSION_FOR_SLITHER_API], check=True, capture_output=True, text=True)
        print(f"  Successfully ran 'solc-select use {SOLC_VERSION_FOR_SLITHER_API}'. Slither might use this context.")
    except FileNotFoundError:
        print(f"  Warning: 'solc-select' command not found. Ensure it's installed and in PATH if relying on it globally.")
    except subprocess.CalledProcessError as e:
        print(f"  Warning: 'solc-select use {SOLC_VERSION_FOR_SLITHER_API}' failed. Error: {e.stderr.strip()}")
        print(f"  Ensure solc version {SOLC_VERSION_FOR_SLITHER_API} is installed via 'solc-select install {SOLC_VERSION_FOR_SLITHER_API}'.")
        print(f"  Slither will rely on 'solc_solcs_select' parameter or its default compiler finding logic.")
    # --- End Optional solc-select check ---

    successful_extractions = 0
    files_with_no_features = 0
    failed_extractions = 0

    for contract_filename_key, meta_info in metadata.items():
        processed_filepath = meta_info.get("processed_filepath")
        if not processed_filepath or not os.path.exists(processed_filepath):
            print(f"Skipping {contract_filename_key}: processed file path '{processed_filepath}' not found or invalid in metadata.")
            failed_extractions += 1
            # Create an error JSON for this file
            error_features = {"error": "Processed file path not found in metadata or file does not exist.", "contract_file": contract_filename_key}
            error_feature_filename = f"{os.path.splitext(contract_filename_key)[0]}_features.json" # Save as .json to be consistent
            error_feature_filepath = os.path.join(FEATURES_DIR, error_feature_filename)
            try:
                with open(error_feature_filepath, 'w', encoding='utf-8') as f_err:
                    json.dump(error_features, f_err, indent=4)
                print(f"  Error report for {contract_filename_key} saved to {error_feature_filepath}")
            except Exception as e_write:
                 print(f"  CRITICAL: Failed to write error report {error_feature_filepath}: {e_write}")
            continue

        print(f"Processing {processed_filepath}...")
        contract_features_for_file = {} # Stores features for all contracts within this one .sol file

        try:
            from slither import Slither
            from slither.exceptions import SlitherError # To catch Slither-specific compilation issues
            # from slither.core.declarations.modifier import Modifier # For isinstance check, if needed

            slither_instance = Slither(
                processed_filepath,
                solc_solcs_select=SOLC_VERSION_FOR_SLITHER_API,
                disable_fail_on_error=True
            )

            if not slither_instance.contracts:
                print(f"    Warning: Slither API found no contract objects in '{contract_filename_key}'. This could be due to compilation errors (check Slither logs/stderr if persistent), an empty file, or an interface-only file.")
                files_with_no_features += 1
                # Save an empty JSON or a note indicating no contracts found
                contract_features_for_file = {"info": "No contract objects found by Slither.", "contract_file": contract_filename_key}
            else:
                for contract_obj in slither_instance.contracts:
                    # Get a set of modifier names declared in this specific contract object for efficient lookup
                    # contract_obj.modifiers should list ModifierDeclaration instances
                    declared_modifier_names = {m.name for m in contract_obj.modifiers}

                    functions_and_modifiers_info = []
                    for func_or_modifier_obj in contract_obj.functions_and_modifiers:
                        # Determine if this object represents a declared modifier
                        is_declared_modifier = False
                        if hasattr(func_or_modifier_obj, 'is_modifier') and func_or_modifier_obj.is_modifier:
                            # Newer Slither versions might have func_obj.is_modifier
                            is_declared_modifier = True
                        elif func_or_modifier_obj.name in declared_modifier_names:
                            # Fallback: if its name is in the list of declared modifiers for this contract
                            is_declared_modifier = True
                        # You could also add:
                        # elif isinstance(func_or_modifier_obj, Modifier): # If Modifier class is imported
                        #    is_declared_modifier = True


                        # Get modifiers *applied to* this function/modifier
                        # func_or_modifier_obj.modifiers should list ModifierSolidity objects (or similar) that are applied
                        applied_modifiers_names = [m.name for m in func_or_modifier_obj.modifiers]

                        functions_and_modifiers_info.append({
                            "name": func_or_modifier_obj.full_name, # e.g., "MyContract.myFunction" or "MyContract.myModifier"
                            "signature": func_or_modifier_obj.signature_str, # e.g., "myFunction(uint256)"
                            "visibility": func_or_modifier_obj.visibility,
                            "is_constructor": func_or_modifier_obj.is_constructor,
                            "is_declared_modifier": is_declared_modifier, # True if this object itself is a modifier declaration
                            "applied_modifiers": applied_modifiers_names, # Modifiers *used by* this function/constructor/modifier
                            "is_payable": func_or_modifier_obj.payable,
                            "is_view": func_or_modifier_obj.view, # Slither maps 'constant' to 'view' for 0.4.x
                            "is_pure": func_or_modifier_obj.pure,
                            "parameters": [f"{str(v.type)} {v.name}" for v in func_or_modifier_obj.parameters],
                            "return_values": [f"{str(v.type)} {v.name if v.name else ''}" for v in func_or_modifier_obj.return_values],
                            # "node_entry_point_id": func_or_modifier_obj.entry_point.node_id if func_or_modifier_obj.entry_point else None, # Example for CFG
                        })

                    state_vars_info = []
                    for var_obj in contract_obj.state_variables:
                        state_vars_info.append({
                            "name": var_obj.name,
                            "type": str(var_obj.type),
                            "visibility": var_obj.visibility,
                            "is_constant": var_obj.is_constant,
                            "is_immutable": var_obj.is_immutable,
                            # "initial_value_expression": str(var_obj.expression) if var_obj.expression else None,
                        })

                    # Store features for this specific contract object within the file
                    contract_features_for_file[contract_obj.name] = {
                        "contract_name_in_file": contract_obj.name,
                        "kind": contract_obj.contract_kind,
                        "inheritance": [c.name for c in contract_obj.inheritance],
                        "is_fully_implemented": contract_obj.is_fully_implemented,
                        "defined_functions_and_modifiers": functions_and_modifiers_info,
                        "defined_state_variables": state_vars_info,
                        # "defined_events": [{ "name": e.name, "signature": e.full_name } for e in contract_obj.events],
                        # "defined_structs": [s.name for s in contract_obj.structs_as_dict.values()], # or contract_obj.structs
                        # "defined_enums": [e.name for e in contract_obj.enums_as_dict.values()], # or contract_obj.enums
                    }

                if contract_features_for_file: # If any contract features were extracted from this file
                    successful_extractions += 1
                else: # Should only happen if slither_instance.contracts was empty initially
                      # This case is already handled by the "files_with_no_features" counter
                    pass


        except ImportError:
            print(f"CRITICAL: Slither Python API not found for {contract_filename_key}. Ensure 'slither-analyzer' is installed correctly in the venv.")
            # This is a fatal error for the script; metadata for this file will be an error.
            contract_features_for_file = {"error": "Slither API ImportError", "contract_file": contract_filename_key}
            failed_extractions += 1 # Count as explicit failure to attempt processing
            # To prevent loop from continuing if Slither itself is missing, we can exit:
            # sys.exit(1) # Or handle more gracefully by skipping all subsequent files.
            # For now, we'll let it record the error for this file and try others.
        except SlitherError as se:
            print(f"  SlitherError during feature extraction for {contract_filename_key}: {se}")
            contract_features_for_file = {"error": f"SlitherError: {str(se)}", "contract_file": contract_filename_key}
            failed_extractions += 1
        except Exception as e:
            print(f"  General Error during feature extraction for {contract_filename_key}: {type(e).__name__} - {e}")
            contract_features_for_file = {"error": f"General Error: {type(e).__name__} - {str(e)}", "contract_file": contract_filename_key}
            failed_extractions += 1

        # Save the extracted features (or error/info) for this .sol file
        feature_filename = f"{os.path.splitext(contract_filename_key)[0]}_features.json"
        feature_filepath = os.path.join(FEATURES_DIR, feature_filename)
        try:
            with open(feature_filepath, 'w', encoding='utf-8') as f_feat:
                json.dump(contract_features_for_file, f_feat, indent=4)

            if "error" not in contract_features_for_file and "info" not in contract_features_for_file and contract_features_for_file:
                print(f"  Extracted features saved to {feature_filepath}")
            elif "error" in contract_features_for_file:
                print(f"  Error details for {contract_filename_key} saved to {feature_filepath}")
            elif "info" in contract_features_for_file:
                print(f"  Info (e.g., no contracts found) for {contract_filename_key} saved to {feature_filepath}")
            # else: # contract_features_for_file might be empty if a file had contracts but none had extractable elements (unlikely)
            #    print(f"  No specific features extracted though contracts might exist; empty map saved to {feature_filepath}")

        except Exception as e_write:
            print(f"  CRITICAL: Failed to write feature file {feature_filepath}: {e_write}")
            failed_extractions +=1 # Count as an additional failure if writing the output fails

    print("\n--- Feature Extraction Summary ---")
    print(f"Files with successfully extracted contract features: {successful_extractions}")
    print(f"Files processed by Slither but yielded no contract objects (e.g., interface-only, severe compile issues not caught as error): {files_with_no_features}")
    print(f"Files that caused explicit errors during Slither processing or had missing paths/write errors: {failed_extractions}")
    total_processed_or_attempted = len(metadata)
    print(f"Total files from metadata attempted: {total_processed_or_attempted}")
    print(f"Feature files (or error/info reports) saved in '{FEATURES_DIR}'")

def extract_external_features(contract_path=None):
    """Extract features from an external contract for evaluation"""
    os.makedirs(EXTERNAL_FEATURES_DIR, exist_ok=True)
    
    if contract_path:
        # Process a specific external contract
        contracts = [contract_path]
    else:
        # Process all contracts in the external directory
        contracts = glob(os.path.join(EXTERNAL_DIR, '*.sol'))
    
    if not contracts:
        print(f"No external contracts found in {EXTERNAL_DIR}/")
        return
    
    print(f"Extracting features from {len(contracts)} external contract(s)...")
    
    try:
        from slither import Slither
        from slither.exceptions import SlitherError
        
        for contract_file in contracts:
            print(f"Processing external contract: {contract_file}")
            contract_filename = os.path.basename(contract_file)
            feature_filename = f"{os.path.splitext(contract_filename)[0]}_features.json"
            feature_filepath = os.path.join(EXTERNAL_FEATURES_DIR, feature_filename)
            
            try:
                slither_instance = Slither(
                    contract_file,
                    solc_solcs_select=SOLC_VERSION_FOR_SLITHER_API,
                    disable_fail_on_error=True
                )
                
                contract_features = {}
                
                if not slither_instance.contracts:
                    print(f"  Warning: No contracts found in {contract_filename}")
                    contract_features = {"info": "No contract objects found by Slither.", "contract_file": contract_filename}
                else:
                    for contract_obj in slither_instance.contracts:
                        # Extract features using the same logic as in extract_all_features
                        declared_modifier_names = {m.name for m in contract_obj.modifiers}

                        functions_and_modifiers_info = []
                        for func_or_modifier_obj in contract_obj.functions_and_modifiers:
                            is_declared_modifier = False
                            if hasattr(func_or_modifier_obj, 'is_modifier') and func_or_modifier_obj.is_modifier:
                                is_declared_modifier = True
                            elif func_or_modifier_obj.name in declared_modifier_names:
                                is_declared_modifier = True

                            applied_modifiers_names = [m.name for m in func_or_modifier_obj.modifiers]

                            functions_and_modifiers_info.append({
                                "name": func_or_modifier_obj.full_name,
                                "signature": func_or_modifier_obj.signature_str,
                                "visibility": func_or_modifier_obj.visibility,
                                "is_constructor": func_or_modifier_obj.is_constructor,
                                "is_declared_modifier": is_declared_modifier,
                                "applied_modifiers": applied_modifiers_names,
                                "is_payable": func_or_modifier_obj.payable,
                                "is_view": func_or_modifier_obj.view,
                                "is_pure": func_or_modifier_obj.pure,
                                "parameters": [f"{str(v.type)} {v.name}" for v in func_or_modifier_obj.parameters],
                                "return_values": [f"{str(v.type)} {v.name if v.name else ''}" for v in func_or_modifier_obj.return_values],
                            })

                        state_vars_info = []
                        for var_obj in contract_obj.state_variables:
                            state_vars_info.append({
                                "name": var_obj.name,
                                "type": str(var_obj.type),
                                "visibility": var_obj.visibility,
                                "is_constant": var_obj.is_constant,
                                "is_immutable": var_obj.is_immutable,
                            })

                        contract_features[contract_obj.name] = {
                            "contract_name_in_file": contract_obj.name,
                            "kind": contract_obj.contract_kind,
                            "inheritance": [c.name for c in contract_obj.inheritance],
                            "is_fully_implemented": contract_obj.is_fully_implemented,
                            "defined_functions_and_modifiers": functions_and_modifiers_info,
                            "defined_state_variables": state_vars_info,
                        }
                
                with open(feature_filepath, 'w', encoding='utf-8') as f_feat:
                    json.dump(contract_features, f_feat, indent=4)
                print(f"  Extracted features saved to {feature_filepath}")
                
            except SlitherError as se:
                print(f"  SlitherError while processing {contract_filename}: {se}")
                contract_features = {"error": f"SlitherError: {str(se)}", "contract_file": contract_filename}
                with open(feature_filepath, 'w', encoding='utf-8') as f_feat:
                    json.dump(contract_features, f_feat, indent=4)
            except Exception as e:
                print(f"  Error while processing {contract_filename}: {e}")
                contract_features = {"error": f"Error: {str(e)}", "contract_file": contract_filename}
                with open(feature_filepath, 'w', encoding='utf-8') as f_feat:
                    json.dump(contract_features, f_feat, indent=4)
                    
    except ImportError:
        print("CRITICAL ERROR: Slither module not found. Please install slither-analyzer.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract features from smart contracts')
    parser.add_argument('--external', action='store_true', help='Extract features from external contracts')
    parser.add_argument('--contract', type=str, help='Path to a specific external contract')
    
    args = parser.parse_args()
    
    # Basic check for slither module availability before starting
    try:
        import slither
        print("Slither module found.")
        
        if args.external:
            extract_external_features()
        elif args.contract:
            extract_external_features(args.contract)
        else:
            print("Starting feature extraction for training data...")
            extract_all_features()
    except ImportError:
        print("CRITICAL ERROR: Slither module not found. Please install slither-analyzer.")
        print("Run: pip install slither-analyzer")
        sys.exit(1)