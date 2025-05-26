# evaluate_external.py
"""
Script to evaluate external smart contracts using the trained model.
This is the main entry point for analyzing new contracts.
"""
import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Evaluate external smart contracts for loopholes')
    parser.add_argument('contract_path', type=str, help='Path to the smart contract file (.sol)')
    parser.add_argument('--skip-training', action='store_true', help='Skip training phase and use existing model')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.contract_path):
        print(f"Error: Contract file not found: {args.contract_path}")
        sys.exit(1)
    
    if not args.contract_path.endswith('.sol'):
        print(f"Warning: File {args.contract_path} does not have a .sol extension. Is this a Solidity file?")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Create necessary directories
    os.makedirs('External_Contracts', exist_ok=True)
    os.makedirs(os.path.join('External_Results', 'features'), exist_ok=True)
    os.makedirs(os.path.join('External_Results', 'detections'), exist_ok=True)
    os.makedirs(os.path.join('External_Results', 'reports'), exist_ok=True)
    os.makedirs('Models', exist_ok=True)
    
    # If we don't have a trained model or --skip-training is not set, run the training pipeline
    if not args.skip_training or not os.path.exists(os.path.join('Models', 'vulnerability_patterns.json')):
        print("Running training pipeline to build vulnerability model...")
        
        # Check if we have training data
        if not os.path.exists('Preprocessed_Contracts') or len(os.listdir('Preprocessed_Contracts')) == 0:
            print("No training data found. Running preprocessing...")
            subprocess.run(['python', 'data_preprocessing.py'])
        
        # Extract features and detect loopholes if needed
        if not os.path.exists('Detection_Results') or len(os.listdir('Detection_Results')) == 0:
            if not os.path.exists('Extracted_Features') or len(os.listdir('Extracted_Features')) == 0:
                print("Extracting features from training contracts...")
                subprocess.run(['python', 'feature_extraction.py'])
            
            print("Detecting loopholes in training contracts...")
            subprocess.run(['python', 'loophole_detection.py'])
        
        # Train model
        print("Training vulnerability model...")
        subprocess.run(['python', 'train_model.py'])
    
    # Process the external contract
    print(f"\nEvaluating external contract: {args.contract_path}")
    
    # Step 1: Preprocess the contract
    print("Step 1: Preprocessing contract...")
    subprocess.run(['python', 'data_preprocessing.py', '--external', args.contract_path])
    
    # Step 2: Extract features
    print("Step 2: Extracting features...")
    subprocess.run(['python', 'feature_extraction.py', '--contract', args.contract_path])
    
    # Step 3: Detect loopholes
    print("Step 3: Detecting loopholes...")
    subprocess.run(['python', 'loophole_detection.py', '--contract', args.contract_path])
    
    # Step 4: Generate report
    print("Step 4: Generating report...")
    subprocess.run(['python', 'generate_report.py', '--contract', args.contract_path])
    
    # Get the report filename
    contract_name = os.path.splitext(os.path.basename(args.contract_path))[0]
    report_path = os.path.join('External_Results', 'reports', f"{contract_name}_report.md")
    
    if os.path.exists(report_path):
        print(f"\nEvaluation complete! Report generated at: {report_path}")
        
        # Show a summary of the findings
        try:
            with open(report_path, 'r') as f:
                lines = f.readlines()
                
            # Find and print the summary section
            print("\nSummary of findings:")
            summary_start = False
            for line in lines:
                if "## Summary" in line:
                    summary_start = True
                    continue
                
                if summary_start and line.strip() == "":
                    continue
                    
                if summary_start and line.startswith("##"):
                    break
                    
                if summary_start:
                    print(line.strip())
        except Exception as e:
            print(f"Error reading report: {e}")
    else:
        print(f"Evaluation complete, but report file was not found at expected location: {report_path}")

if __name__ == "__main__":
    main()
