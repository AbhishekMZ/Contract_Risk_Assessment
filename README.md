# Smart Contract Loophole Detection Pipeline

This project provides a modular pipeline for detecting vulnerabilities (loopholes) in Ethereum smart contracts using both static analysis and machine learning. It supports both training on a dataset of contracts and evaluating external contracts.

## Features
- **Preprocessing**: Cleans and prepares Solidity contracts for analysis.
- **Feature Extraction**: Extracts features for ML-based detection.
- **Loophole Detection**: Uses Slither and custom rules to find vulnerabilities.
- **Report Generation**: Human-readable reports for both training and external contracts.
- **Model Training**: Learns vulnerability patterns from your dataset.
- **Evaluation**: Analyze new contracts using trained models.

## Directory Structure
```
Contract_Eval/
├── SmartContracts/           # Training contracts (input)
├── Preprocessed_Contracts/   # Preprocessed training contracts
├── Extracted_Features/       # Extracted features from training contracts
├── Detection_Results/        # Detection results for training
├── Reports/                  # Reports for training contracts
├── Models/                   # Trained ML models
├── External_Contracts/       # External contracts to evaluate
├── External_Results/         # Results for external contracts
│   ├── features/
│   ├── detections/
│   └── reports/
├── *.py                     # Pipeline scripts
├── requirements.txt
├── README.md
└── .gitignore
```

## Getting Started
1. **Clone the repo**
   ```
   git clone https://github.com/AbhishekMZ/Contract_Risk_Assessment.git
   cd Contract_Risk_Assessment
   ```
2. **Install dependencies**
   ```
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. **Add training contracts**
   - Place your Solidity `.sol` files in the `SmartContracts/` directory.

4. **Run the training pipeline**
   ```
   python main_pipeline.py --train
   ```

5. **Evaluate an external contract**
   ```
   python main_pipeline.py --evaluate path/to/contract.sol
   ```

## Notes
- Requires Python 3.7+
- Slither must be installed and available in your environment for static analysis.
- For best results, use a clean dataset and review generated reports for accuracy.

## Contributing
Feel free to fork, open issues, or submit pull requests to improve the pipeline!
