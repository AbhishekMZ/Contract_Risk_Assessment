# Installation Guide

This guide will help you set up the Smart Contract Security Analyzer for local development and production deployment.

## Prerequisites

- **For Development:**
  - Python 3.9 or higher
  - Node.js 16.x or higher
  - npm or yarn
  - Git

- **For Production (Docker):**
  - Docker 20.10+
  - Docker Compose 1.29+

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/contract-analyzer.git
cd contract-analyzer
```

### 2. Set Up Backend

1. Create and activate a Python virtual environment:
   ```bash
   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### 3. Set Up Frontend

1. Navigate to the frontend directory and install dependencies:
   ```bash
   cd ../frontend
   npm install
   # or
   yarn
   ```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration.

## Running the Application

### Development Mode

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. In a new terminal, start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   # or
   yarn dev
   ```

3. Open your browser to `http://localhost:3000`

### Using Docker (Development)

1. Make sure Docker is running
2. From the project root, run:
   ```bash
   docker-compose up --build
   ```
3. Access the application at `http://localhost:3000`

## Production Deployment

### Using Docker Compose (Recommended)

1. Set up your production environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. Build and start the containers:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. The application will be available at `http://your-server-ip:3000`

### Manual Deployment

1. **Backend:**
   - Set up a production WSGI server (e.g., Gunicorn with Nginx)
   - Configure environment variables
   - Run database migrations

2. **Frontend:**
   - Build the production bundle: `npm run build`
   - Serve the `dist` directory using a web server like Nginx

## API Documentation

When the backend is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Troubleshooting

- **Port conflicts**: Ensure ports 3000 (frontend), 8000 (backend), and 5432 (database) are available
- **Docker issues**: Try rebuilding the containers with `docker-compose build --no-cache`
- **Dependency issues**: Delete `node_modules` and reinstall with `npm install` or `yarn`

## Support

For issues and feature requests, please use the [issue tracker](https://github.com/yourusername/contract-analyzer/issues).
