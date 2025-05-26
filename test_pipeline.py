# test_pipeline.py
"""
Simple script to test the smart contract loophole detection pipeline.
This provides a convenient way to verify that all components work together correctly.
"""
import os
import sys
import argparse
import subprocess

def create_test_contract(output_path="test_contract.sol"):
    """Create a simple test contract to use for testing the pipeline"""
    print(f"Creating test contract at {output_path}...")
    test_contract = """// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Reentrancy {
    mapping(address => uint) private userBalances;

    function deposit() public payable {
        userBalances[msg.sender] += msg.value;
    }

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // This is vulnerable to reentrancy
        if (msg.sender.call.value(amountToWithdraw)()) {
            userBalances[msg.sender] = 0;
        }
    }
}
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(test_contract)
    return os.path.abspath(output_path)

def test_training_pipeline():
    """Test the training pipeline by running it with default settings"""
    print("\n===== Testing Training Pipeline =====")
    result = subprocess.run([sys.executable, "main_pipeline.py", "--train"], check=False)
    if result.returncode == 0:
        print("✅ Training pipeline test passed!")
    else:
        print("❌ Training pipeline test failed!")

def test_evaluation_pipeline(contract_path):
    """Test the evaluation pipeline by running it on a test contract"""
    print(f"\n===== Testing Evaluation Pipeline on {contract_path} =====")
    result = subprocess.run([sys.executable, "main_pipeline.py", "--evaluate", contract_path], check=False)
    if result.returncode == 0:
        print("✅ Evaluation pipeline test passed!")
        report_path = os.path.join("External_Results", "reports", f"{os.path.splitext(os.path.basename(contract_path))[0]}_report.md")
        if os.path.exists(report_path):
            print(f"Report generated at: {report_path}")
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
                print("\nReport preview:")
                print("----------------")
                print("\n".join(report_content.split("\n")[:10]) + "\n...")
        else:
            print(f"❌ Expected report not found at {report_path}")
    else:
        print("❌ Evaluation pipeline test failed!")

def main():
    parser = argparse.ArgumentParser(description="Test the smart contract loophole detection pipeline")
    parser.add_argument("--mode", choices=["train", "evaluate", "both"], default="both", 
                        help="Pipeline mode to test: train, evaluate, or both")
    parser.add_argument("--contract", type=str, help="Path to a contract to use for evaluation testing")
    
    args = parser.parse_args()
    
    # Create a test contract if needed
    contract_path = args.contract
    if not contract_path and (args.mode == "evaluate" or args.mode == "both"):
        contract_path = create_test_contract()
    
    # Run the tests
    if args.mode == "train" or args.mode == "both":
        test_training_pipeline()
    
    if args.mode == "evaluate" or args.mode == "both":
        if contract_path:
            test_evaluation_pipeline(contract_path)
        else:
            print("❌ No contract specified for evaluation test")
    
    if args.mode == "both":
        print("\n===== All Tests Complete =====")

if __name__ == "__main__":
    main()
