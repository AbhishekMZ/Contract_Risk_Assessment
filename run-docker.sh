#!/bin/bash

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit the .env file with your configuration and run this script again."
    exit 1
fi

# Build and start containers
echo "Starting application with Docker Compose..."
docker-compose up --build -d

echo ""
echo "Application is running!"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- pgAdmin: http://localhost:5050"
echo ""
echo "To stop the application, run: docker-compose down"
