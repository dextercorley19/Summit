# GitHub MCP Backend

Backend for the GitHub MCP product, providing API endpoints to interact with GitHub repositories using AI agents.

## Features

- GitHub authentication with personal access tokens
- Repository listing and browsing
- Chat interface with memory for repository analysis using GitHub MCP server
- AI-powered repository analysis using Pydantic AI agents

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   PORT=8000
   ```

## Running the Backend

To run the backend in development mode:

```
cd backend
python app.py
```

This will start the server at http://localhost:8000 with auto-reload enabled.

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/auth/github` - Authenticate with GitHub token and get repositories

### Repositories

- `GET /api/repositories` - Get all repositories for the authenticated user
- `GET /api/repositories/{repo_name}/branches` - Get branches for a repository
- `GET /api/repositories/{repo_name}/contents` - Get contents of a repository
- `GET /api/repositories/{repo_name}/file` - Get content of a specific file

### Chat

- `POST /api/chat` - Chat with repository using AI
- `GET /api/chat/history/{repo_name}` - Get conversation history for a repository
- `GET /api/chat/{conversation_id}` - Get a specific conversation

## Requirements

- Python 3.9+
- Docker (for running the GitHub MCP server)
- GitHub Personal Access Token with appropriate permissions 