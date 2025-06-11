#!/bin/bash

# Create and activate Python virtual environment
echo "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install Python dependencies
echo "Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
cd ../frontend
npm install

# Create .env file if it doesn't exist
cd ..
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit the .env file with your configuration."
fi

echo "Development environment setup complete!"
echo "To start the application, run:"
echo "1. Backend: cd backend && uvicorn main:app --reload"
echo "2. Frontend: cd frontend && npm run dev"
