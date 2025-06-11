# Smart Contract Security Analyzer

A comprehensive tool for detecting vulnerabilities in Ethereum smart contracts using static analysis and pattern recognition. This project includes a modern web interface for easy interaction with the analysis pipeline, allowing users to upload and analyze smart contracts with a simple, intuitive workflow.

## Features

### Core Features
- **Smart Contract Analysis**: Upload and analyze Solidity contracts for security vulnerabilities
- **Pattern Detection**: Uses regex and rule-based patterns to detect common vulnerabilities
- **Multi-Format Support**: Analyze uploaded .sol files or paste contract code directly
- **Asynchronous Processing**: Background processing ensures UI remains responsive
- **Interactive Reports**: Detailed results with vulnerability severity classification

### Technical Features
- **Modular Backend**: Built with FastAPI for high performance and scalability
- **Modern Frontend**: Responsive React application with TypeScript and TailwindCSS
- **Robust File Handling**: Atomic file operations and retry mechanisms prevent race conditions
- **Error Recovery**: Exponential backoff for improved resilience
- **RESTful API**: Well-documented endpoints for integration with other tools
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Project Structure

```
Contract_Eval/
├── backend/                 # FastAPI backend
│   ├── core/                # Core analysis logic
│   │   ├── analysis/        # Vulnerability detection & analysis
│   │   └── utils/           # Utility functions
│   ├── models/              # Data models and schemas
│   ├── config/              # Configuration settings
│   ├── uploads/             # Temporary storage for uploaded contracts
│   ├── results/             # Analysis results storage
│   └── main.py              # API entry point with FastAPI app
│
├── frontend/               # React/TypeScript frontend
│   ├── public/              # Static assets
│   └── src/                 # Source code
│       ├── components/      # Reusable UI components
│       │   └── FileUpload/  # Contract upload component
│       ├── pages/           # Page components
│       ├── services/        # API services
│       │   └── api.ts       # API client with polling mechanism
│       └── assets/          # Images, styles, etc.
│
├── Documentation/          # Project documentation
│   └── future_implementations.md  # Planned enhancements
│
├── SmartContracts/         # Example smart contracts
├── Detection_Results/      # Analysis results
├── External_Contracts/     # External contracts to evaluate
├── docker-compose.yml      # Docker configuration
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── .gitignore              # Git ignore rules
```

## Installation & Setup

### Prerequisites
- Python 3.8+ 
- Node.js 14+ and npm/yarn
- Git

### Backend Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/AbhishekMZ/Contract_Eval.git
   cd Contract_Eval
   ```

2. **Create a virtual environment**
   ```bash
   # For Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # For macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Start the backend server**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   The API will be available at http://localhost:8000

### Frontend Setup

1. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   # or
   yarn install
   ```

2. **Start the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```
   The frontend will be available at http://localhost:3000

### Using Docker (Alternative)

```bash
docker-compose up -d
```

## Usage

### Web Interface
1. Navigate to http://localhost:3000 in your browser
2. Upload a Solidity contract file (.sol) or paste contract code directly
3. Click "Analyze Contract"
4. Wait for the analysis to complete
5. View detailed vulnerability report

### API Endpoints

- **POST /api/upload**: Upload a contract file
- **POST /api/analyze**: Analyze a contract (by file ID or direct code)
- **GET /api/analysis/{analysis_id}/status**: Check analysis status
- **GET /api/analysis/{analysis_id}**: Get analysis results

## Development Notes

- The backend uses atomic file operations to prevent race conditions when saving analysis results
- The frontend implements polling with exponential backoff for checking analysis status
- File uploads are stored with unique IDs in the `uploads` directory
- Analysis results are saved as JSON files in the `results` directory

## Contributing
Feel free to fork, open issues, or submit pull requests to improve the pipeline!
