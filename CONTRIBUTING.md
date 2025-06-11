# Contributing to Smart Contract Security Analyzer

Thank you for considering contributing to the Smart Contract Security Analyzer! This document outlines the process for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in the Issues section
- Use the bug report template if available
- Include detailed steps to reproduce the issue
- Include relevant details about your environment

### Suggesting Enhancements

- Check if the enhancement has already been suggested in the Issues section
- Provide a clear description of the enhancement
- Explain why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Submit a pull request

## Development Setup

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/AbhishekMZ/Contract_Eval.git
cd Contract_Eval

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start the backend server
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Coding Guidelines

- Follow PEP 8 style guidelines for Python code
- Use TypeScript for frontend code
- Write tests for new functionality
- Document new functions and components

## Testing

- Run backend tests: `pytest`
- Run frontend tests: `npm test`

## Documentation

- Update documentation when changing functionality
- Document new features thoroughly
- Use docstrings for Python functions and classes

## Commit Messages

Use clear, descriptive commit messages:
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues and pull requests when relevant

Thank you for your contributions!
