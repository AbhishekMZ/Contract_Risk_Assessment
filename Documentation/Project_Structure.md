# Contract Risk Assessment - Project Structure

This document outlines the structure of the Contract Risk Assessment system after the consolidation of redundant components and improvements to key functionality.

## Overview

The Contract Risk Assessment system is a web application built with Flask that analyzes legal and smart contracts to identify potential risks, vulnerabilities, and important clauses. It uses a combination of NLP techniques, machine learning, and specialized security analysis tools to provide comprehensive risk assessments.

The application supports:

- Asynchronous processing with Celery and Redis
- Analysis of both legal contracts (PDF, DOCX, TXT) and smart contracts (Solidity)
- Risk scoring based on configurable patterns
- Security analysis using specialized tools
- Real-time task status updates via the API

## Directory Structure

```
Contract_Eval/
├── Flask/                      # Web application code
│   ├── app/                    # Flask application
│   │   ├── templates/          # HTML templates
│   │   ├── static/             # Static assets (JS, CSS)
│   │   ├── views/              # Route handlers
│   │   ├── __init__.py         # Application initialization
│   │   ├── imp_celery_app.py   # Celery configuration
│   │   ├── imp_celery_config.py # Celery task configuration
│   │   ├── imp_models.py       # Database models
│   │   └── imp_tasks.py        # Celery tasks
│   └── config.py               # Application configuration
├── src/                        # Analysis modules
│   └── contract_analysis/      # Contract analysis components
│       ├── imp_pipeline.py     # Contract parsing and analysis pipeline
│       ├── imp_risk_scorer.py  # Risk assessment modules
│       └── imp_tools_integration.py # Integration with security tools
├── models/                     # ML models
├── config/                     # Configuration files
│   └── legal_risk_patterns.json # Legal risk pattern definitions
└── Documentation/              # Project documentation
```

## Key Components

### Flask Application

#### Core Application (`Flask/app/__init__.py`)

- Initializes Flask application with Celery integration
- Registers blueprints for different areas of functionality
- Configures error handling and CORS

#### Database Models (`Flask/app/imp_models.py`)

- `User`: Authentication and user data
- `Contract`: Uploaded contract files and metadata
- `Analysis`: Stores analysis results and task status

#### API Endpoints (`Flask/app/views/imp_api.py`)

- `/api/contracts`: Upload and list contracts
- `/api/contracts/<id>`: Get contract details
- `/api/contracts/<id>/analysis`: Request analysis
- `/api/tasks/<task_id>`: Check status of analysis tasks

#### Asynchronous Processing

- `imp_celery_app.py`: Creates Celery application with Flask context
- `imp_celery_config.py`: Configures Celery behavior and Redis connection
- `imp_tasks.py`: Implements asynchronous contract analysis tasks

#### Dashboard (`Flask/app/views/imp_dashboard.py`)

- Contract dashboard for viewing and analyzing contracts
- Analytics view for aggregate risk metrics

### Analysis Components

#### Pipeline (`src/contract_analysis/imp_pipeline.py`)

- `ContractParser`: Base class for contract parsing
- `LegalContractParser`: PDF/DOCX parser with improved text extraction
- `SmartContractParser`: Solidity contract parser
- `ContractAnalysisPipeline`: Unified analysis pipeline for all contract types

#### Risk Scoring (`src/contract_analysis/imp_risk_scorer.py`)

- `RiskScore`: Container for risk assessment results
- `LegalContractRiskScorer`: Configuration-based pattern matching for legal risk
- `SmartContractRiskScorer`: Smart contract vulnerability detection

#### Security Tools (`src/contract_analysis/imp_tools_integration.py`)

- `SecurityAnalysisTool`: Base class for security analysis tools
- `MythrilAnalyzer`: Integration with Mythril for smart contract security
- `SmartCheckAnalyzer`: Integration with SmartCheck
- `OyenteAnalyzer`: Integration with Oyente
- `MultiToolAnalyzer`: Combines results from multiple security tools

## Workflow

1. User uploads a contract through the web interface or API
2. The contract is saved and a Celery task is scheduled for analysis
3. The task uses the `ContractAnalysisPipeline` to:
   - Determine the contract type
   - Extract text and metadata
   - Parse the contract structure
   - Identify entities and sections
   - Analyze for risks and vulnerabilities
   - Score overall risk level
4. Results are stored in the database
5. User views analysis results through dashboard or API

## Configuration

### Risk Pattern Configuration

Legal contract risk patterns can be customized through the `config/legal_risk_patterns.json` file:

```json
{
  "missing_clauses": {
    "termination": {
      "keywords": ["termination", "terminate", "end of agreement"],
      "regex_patterns": ["(?i)termination\\s+clause"],
      "risk_level": "HIGH",
      "description": "Missing termination clause",
      "category": "Completeness",
      "remediation": "Add a termination clause"
    }
  }
}
```

### Application Configuration

The Flask application is configured through `config.py`:

- Database connection
- Redis connection for Celery
- File upload settings
- Security settings

## Improvements in the Enhanced Implementation

1. **Asynchronous Processing**: Tasks now run in the background with Celery, providing better scalability.

2. **Enhanced Document Processing**: 
   - Better error handling for document extraction
   - Improved heuristics for section detection
   - Table extraction from DOCX files

3. **Configurable Risk Detection**:
   - Pattern-based risk detection using keywords and regex
   - Configuration files for easy customization

4. **Enhanced Security Tool Integration**:
   - Better error handling and timeout management
   - XML/JSON parsing with fallbacks
   - Combined results from multiple tools

5. **Improved User Experience**:
   - Real-time task status updates
   - Enhanced dashboard with filtering
   - Better visualization of risk factors

6. **Unified Analysis Pipeline**:
   - Consistent API for different contract types
   - Comprehensive metadata extraction
   - Detailed results structure

These improvements make the system more maintainable, extensible, and user-friendly while providing more accurate and comprehensive contract analysis.
