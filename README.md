# Summit

## Local Development Setup

This project consists of a Next.js frontend (`summit-app`) and a FastAPI backend (`summit-app/backend`).

### Setup Instructions

2.  **Setup Frontend (`summit-app`):**
    *   Navigate to the frontend directory:
        ```bash
        cd summit-app
        ```
    *   Install dependencies:
        ```bash
        pnpm install
        ```
    *   Create a `.env.local` file by copying the example if one exists, or create a new one and add the following:
        ```env
        NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
        NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<your_clerk_publishable_key>
        CLERK_SECRET_KEY=<your_clerk_secret_key>

        ```
        *Note: Clerk variables are needed if you are using Clerk for authentication. Adjust if using a different auth provider.*

3.  **Setup Backend (`summit-app/backend`):**
    *   Navigate to the backend directory:
        ```bash
        cd backend
        ```
    *   Create a virtual environment (optional but recommended):
        ```bash
        python -m venv venv
        source venv/bin/activate
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```

### Running the Application

1.  **Start the Backend Server:**
    *   Ensure you are in the `summit-app/backend` directory.
    *   Run the FastAPI application:
        ```bash
        uvicorn app:app --reload --host 0.0.0.0 --port 8000
        ```


2.  **Start the Frontend Development Server:**
    *   Navigate to the `summit-app` directory.
    *   Run the Next.js development server:
        ```bash
        pnpm dev
        ```

The frontend should now be accessible at `http://localhost:3000` and the backend at `http://localhost:8000`.

