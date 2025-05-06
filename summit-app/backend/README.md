# GitHub Repository Analyzer Backend

This is a FastAPI backend service that analyzes GitHub repositories using AI.

## Features

- List GitHub repositories
- Analyze repository code quality
- Chat with AI about repositories

## Setup

### Prerequisites

- Python 3.10+
- Docker
- GitHub Personal Access Token with repo scope

### Installation

1. Clone the repository
2. Create a `.env` file from the example:
   \`\`\`
   cp .env.example .env
   \`\`\`
3. Add your GitHub token to the `.env` file
4. Install dependencies:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`

### Running the Application

#### Using Python

\`\`\`bash
python run.py
\`\`\`

#### Using Docker

\`\`\`bash
docker-compose up -d
\`\`\`

## API Endpoints

- `GET /api/repositories` - List GitHub repositories
- `POST /api/analyze` - Analyze a repository
- `POST /api/chat` - Chat about a repository

## Environment Variables

- `GITHUB_PERSONAL_ACCESS_TOKEN` - Your GitHub Personal Access Token

## Development

To run the application in development mode with auto-reload:

\`\`\`bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
