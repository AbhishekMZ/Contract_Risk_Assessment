# Contract Risk Assessment - User Guide

This guide provides instructions for using the Contract Risk Assessment system with its improved components.

## Getting Started

### System Requirements

- Python 3.8 or higher
- Redis server (for Celery task queue)
- PostgreSQL database
- PDF and DOCX processing libraries

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-org/Contract_Eval.git
   cd Contract_Eval
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the database in `Flask/config.py`

5. Set up environment variables:
   ```
   export FLASK_APP=Flask/app
   export FLASK_ENV=development
   ```

6. Initialize the database:
   ```
   flask db upgrade
   ```

7. Run Redis server:
   ```
   redis-server
   ```

### Starting the Application

1. Start Celery worker:
   ```
   cd Flask
   celery -A app.imp_celery_app.celery worker --loglevel=info
   ```

2. Run Flask application:
   ```
   flask run
   ```

3. Access the application at `http://localhost:5000`

## Using the Application

### User Registration and Login

1. Navigate to `http://localhost:5000/auth/register` to create an account
2. Log in with your credentials at `http://localhost:5000/auth/login`

### Uploading Contracts

1. From the dashboard, click "Upload Contract" or navigate to `http://localhost:5000/main/upload`
2. Select a contract file (supported formats: PDF, DOCX, TXT, SOL)
3. Click "Upload" to submit the contract
4. You'll be redirected to the dashboard where your contract will appear in the list

### Analyzing Contracts

1. From the dashboard, find your contract in the list
2. Click the "Analyze" button next to the contract
3. The analysis will begin asynchronously in the background
4. The status will update in real-time (Pending → In Progress → Completed)

### Viewing Analysis Results

1. Once analysis is complete, click on the contract in the list
2. The contract details panel will show:
   - Basic contract metadata
   - Risk assessment summary with risk level
   - Identified clauses and entities
   - Security vulnerabilities (for smart contracts)
   - Risk details by category

3. Use the filters at the top of the contract list to search for specific contracts

### Understanding Risk Assessment

The risk assessment provides several key pieces of information:

- **Overall Risk Level**: None, Low, Medium, High, or Critical
- **Risk Categories**: Categorized findings (e.g., Completeness, Clarity, Security)
- **Vulnerabilities**: Specific issues found in the contract
- **Recommendations**: Suggestions for addressing each risk

#### Risk Indicators

- 🟢 **None/Low Risk**: Minor issues or no issues detected
- 🟡 **Medium Risk**: Notable issues that should be reviewed
- 🟠 **High Risk**: Significant issues requiring attention
- 🔴 **Critical Risk**: Severe issues requiring immediate attention

## API Usage

The system provides a RESTful API for programmatic contract analysis.

### Authentication

All API endpoints require authentication. Use Basic Auth with your username and password.

### Endpoints

#### List Contracts

```
GET /api/contracts
```

Response:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "example_contract.pdf",
      "status": "COMPLETED",
      "created_at": "2025-05-18T14:30:00Z"
    }
  ]
}
```

#### Upload Contract

```
POST /api/contracts
Content-Type: multipart/form-data
```

Form fields:
- `file`: Contract file (PDF, DOCX, TXT, SOL)

Response:
```json
{
  "status": "success",
  "data": {
    "id": 2,
    "name": "new_contract.pdf",
    "status": "PENDING"
  }
}
```

#### Request Analysis

```
POST /api/contracts/2/analysis
```

Response:
```json
{
  "status": "success",
  "data": {
    "task_id": "7f98c3a4-6b1d-4f28-82b0-45c1a97123456"
  }
}
```

#### Check Task Status

```
GET /api/tasks/7f98c3a4-6b1d-4f28-82b0-45c1a97123456
```

Response:
```json
{
  "status": "success",
  "data": {
    "task_id": "7f98c3a4-6b1d-4f28-82b0-45c1a97123456",
    "status": "SUCCESS",
    "result": { "contract_type": "legal_contract", ... }
  }
}
```

## Customizing Risk Patterns

You can customize the risk detection patterns for legal contracts by modifying the `config/legal_risk_patterns.json` file.

Each pattern includes:
- `keywords`: List of terms to search for
- `regex_patterns`: Regular expressions for more complex matching
- `risk_level`: The severity level (NONE, LOW, MEDIUM, HIGH, CRITICAL)
- `description`: Description of the risk
- `category`: Risk category for grouping
- `remediation`: Suggested action to address the risk

Example pattern configuration:
```json
{
  "missing_clauses": {
    "force_majeure": {
      "keywords": ["force majeure", "act of god"],
      "regex_patterns": ["(?i)force\\s+majeure\\s+clause"],
      "risk_level": "HIGH",
      "description": "Missing force majeure clause",
      "category": "Completeness",
      "remediation": "Add a force majeure clause to address unforeseeable circumstances"
    }
  }
}
```

## Troubleshooting

### Analysis Stuck in "Pending" State

1. Ensure the Celery worker is running
2. Check Redis server is operational
3. View Celery logs for any errors

### File Upload Errors

1. Verify file format is supported
2. Check file size is under the limit (default: 10MB)
3. Ensure the upload directory is writable

### Database Connection Issues

1. Verify PostgreSQL server is running
2. Check database connection settings in `Flask/config.py`
3. Ensure database migration has been applied

## Conclusion

The improved Contract Risk Assessment system provides a comprehensive solution for analyzing both legal and smart contracts. The asynchronous processing, enhanced risk detection, and improved user interface make it a powerful tool for contract analysis.

For more information, refer to:
- [Project Structure](./Project_Structure.md) - Overview of system architecture
- [Redundancy Cleanup](../Understanding/Redundancy_Cleanup.md) - Guide for cleanup of redundant files
