# main_pipeline.py
"""
Run the smart contract loophole detection pipeline.
Supports both training mode for initial data and evaluation mode for external contracts.
"""
import subprocess
import argparse
import os
import sys

# --- Configuration ---
# Directories required for the pipeline
# Note: "SmartContracts" (no space) is used here, ensure consistency with data_preprocessing.py
REQUIRED_DIRECTORIES = [
    "SmartContracts",        # Contains .sol files for the main dataset (training/default mode)
    "Preprocessed_Contracts", # For main dataset
    "Extracted_Features",     # For main dataset
    "Detection_Results",      # For main dataset
    "Reports",                # For main dataset
    "Models",                 # For trained ML models (if train_model.py is used)
    "External_Contracts",     # Input for individual external contracts to evaluate
    "External_Results"        # Output for evaluation of external contracts
]

# Python executable to use for running scripts (ensures same environment)
PYTHON_EXECUTABLE = sys.executable
# Project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Helper Functions ---

def setup_directories():
    """Create required directories if they don't exist."""
    print("Setting up directories...")
    for directory_name in REQUIRED_DIRECTORIES:
        dir_path = os.path.join(PROJECT_ROOT, directory_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}/")

        # Create subdirectories for External_Results if it's being created or already exists
        if directory_name == "External_Results":
            subdirs = ["features", "detections", "reports"]
            for subdir_name in subdirs:
                subdir_path_full = os.path.join(dir_path, subdir_name)
                if not os.path.exists(subdir_path_full):
                    os.makedirs(subdir_path_full, exist_ok=True)
                    print(f"Created directory: {subdir_path_full}/")
    print("Directory setup complete.")


def run_pipeline_step(step_command_list, step_description=""):
    """
    Runs a single pipeline step (a script with arguments).
    step_command_list: A list, e.g., ['python_executable', 'script.py', '--arg1', 'value1']
    step_description: A string to describe the step being run.
    """
    if not step_description:
        step_description = " ".join(os.path.basename(item) for item in step_command_list if '.py' in item or item == PYTHON_EXECUTABLE)
        if not step_description: # Fallback if no .py file found
            step_description = " ".join(step_command_list)


    print(f"\n{'='*10} RUNNING STEP: {step_description} {'='*10}")
    print(f"Executing command: {' '.join(step_command_list)}")

    try:
        process = subprocess.Popen(
            step_command_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,  # Run script from the project root
            text=True # Decodes stdout/stderr as text
        )
        stdout, stderr = process.communicate()

        if stdout:
            print(f"--- STDOUT ---\n{stdout}")
        if stderr:
            # Slither and other tools often print warnings/info to stderr even on success
            print(f"--- STDERR ---\n{stderr}")

        if process.returncode != 0:
            print(f"ERROR: Step '{step_description}' failed with return code {process.returncode}")
            return False
        print(f"SUCCESS: Step '{step_description}' completed.")
        return True
    except FileNotFoundError:
        script_name = next((item for item in step_command_list if item.endswith('.py')), "Unknown script")
        print(f"ERROR: Script '{script_name}' or executable '{step_command_list[0]}' not found.")
        return False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while running step '{step_description}': {e}")
        return False

# --- Pipeline Modes ---

def run_default_pipeline(visualize=False, use_ml_model=False):
    """
    Run the default pipeline on the 'SmartContracts' dataset.
    This was previously referred to as the 'training' pipeline, but 'default' might be better
    if 'train_model.py' is optional.
    """
    print(f"\n{'#'*20} STARTING DEFAULT PIPELINE {'#'*20}")

    # Check for contracts in SmartContracts folder
    smart_contracts_dir_path = os.path.join(PROJECT_ROOT, "SmartContracts")
    if not os.path.exists(smart_contracts_dir_path) or not os.listdir(smart_contracts_dir_path):
        print(f"\nERROR: The '{smart_contracts_dir_path}' directory is empty or does not exist.")
        print("Please add .sol files to the 'SmartContracts' folder before running the default pipeline.")
        sys.exit(1)
    else:
        print(f"\nFound contracts in '{smart_contracts_dir_path}'. Proceeding with default pipeline...")

    # Define steps for the default pipeline
    # Each step script needs to be adapted to know it's running in "default" mode
    # (i.e., using default input/output directories like Preprocessed_Contracts, etc.)
    default_steps_config = [
        {'script': 'data_preprocessing.py', 'args': []},
        {'script': 'feature_extraction.py', 'args': []},
        {'script': 'loophole_detection.py', 'args': []},
        {'script': 'generate_report.py', 'args': []},
    ]

    if use_ml_model: # If you have a train_model.py and want to include it
        default_steps_config.append({'script': 'train_model.py', 'args': []}) # Assuming it exists
        # Potentially add a predict_with_model.py step after loophole_detection

    if visualize:
        default_steps_config.append({'script': 'visualization_dashboard.py', 'args': []})

    for step_config in default_steps_config:
        command = [PYTHON_EXECUTABLE, os.path.join(PROJECT_ROOT, step_config['script'])] + step_config['args']
        if not run_pipeline_step(command, step_description=step_config['script']):
            print(f"\nDefault pipeline aborted due to error in {step_config['script']}.")
            sys.exit(1)

    print(f"\n{'#'*20} DEFAULT PIPELINE COMPLETED SUCCESSFULLY {'#'*20}")


def run_evaluation_pipeline(external_contract_path):
    """Run the evaluation pipeline on a single external contract."""
    print(f"\n{'#'*20} STARTING EVALUATION PIPELINE FOR: {external_contract_path} {'#'*20}")

    if not os.path.isfile(external_contract_path): # Ensure it's a file
        print(f"Error: External contract path is not a file: {external_contract_path}")
        sys.exit(1)

    # Base name for output files, derived from the input contract name
    contract_basename = os.path.basename(external_contract_path)
    contract_name_no_ext = os.path.splitext(contract_basename)[0]

    # The existing scripts use these directory structures:
    # - External_Contracts/ (for preprocessed external contracts)
    # - External_Results/features/ (for extracted features)
    # - External_Results/detections/ (for detection results)
    # - External_Results/reports/ (for generated reports)

    # Ensure the input contract is copied to a known location for preprocessing, or handled directly
    # For simplicity, let's assume scripts can take a direct file path for evaluation mode.
    # Individual scripts (data_preprocessing, feature_extraction, etc.)
    # will need to be modified to accept --input_file, --output_dir arguments for evaluation mode.

        # Use the existing command-line interface of the scripts
    evaluation_steps_config = [
        {
            'script': 'data_preprocessing.py',
            'args': ['--external', external_contract_path]
        },
        {
            'script': 'feature_extraction.py',
            'args': ['--contract', external_contract_path]
        },
        {
            'script': 'loophole_detection.py',
            'args': ['--contract', external_contract_path]
        },
        {
            'script': 'generate_report.py',
            'args': ['--contract', external_contract_path]
        }
    ]

    # Check if a trained ML model is needed and exists (if ML steps are included)
    # model_path = os.path.join(PROJECT_ROOT, "Models", "your_model_file.pkl") # Example
    # if any("predict_with_model.py" in step['script'] for step in evaluation_steps_config) and not os.path.exists(model_path):
    #     print(f"Warning: ML model ({model_path}) not found. ML prediction step will be skipped or may fail.")
    #     # Optionally, run default pipeline to train model first:
    #     # print("Attempting to run default pipeline to train the model...")
    #     # run_default_pipeline(use_ml_model=True)
    #     # if not os.path.exists(model_path):
    #     #     print("Failed to train/find model. Evaluation pipeline for ML prediction cannot proceed.")
    #     #     sys.exit(1)


    for step_config in evaluation_steps_config:
        command = [PYTHON_EXECUTABLE, os.path.join(PROJECT_ROOT, step_config['script'])] + step_config['args']
        if not run_pipeline_step(command, step_description=f"{step_config['script']} (evaluate)"):
            print(f"\nEvaluation pipeline aborted due to error in {step_config['script']}.")
            sys.exit(1)

    # Use the path structure from the existing scripts
    final_report_path = os.path.join(PROJECT_ROOT, "External_Results", "reports", f"{contract_name_no_ext}_report.md")
    print(f"\n{'#'*20} EVALUATION PIPELINE COMPLETED SUCCESSFULLY {'#'*20}")
    print(f"Evaluation report for '{contract_basename}' available at: {final_report_path}")


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description='Smart Contract Loophole Detection Pipeline')
    parser.add_argument(
        '--train', 
        action='store_true',
        help="Run the training pipeline on SmartContracts/ directory"
    )
    parser.add_argument(
        '--evaluate', 
        type=str,
        help="Path to a single smart contract file to evaluate"
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help="Generate visualizations (applies to training mode)"
    )
    parser.add_argument(
        '--use_ml',
        action='store_true',
        help="Include ML model training/prediction steps"
    )

    args = parser.parse_args()

    # Ensure all directories are ready
    setup_directories()

    if args.evaluate:
        # Evaluate a single external contract
        run_evaluation_pipeline(args.evaluate)
    elif args.train or not (args.evaluate or args.train):
        # Default to training mode if no mode is specified
        visualize = args.visualize
        use_ml = args.use_ml
        run_default_pipeline(visualize, use_ml)

if __name__ == "__main__":
    main()