# Tracker Backend

A FastAPI-based backend for task management, habit tracking, and finance integration, integrated with Supabase and ready for Vercel deployment.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd tracker-backend
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables**:
    Copy `.env.example` to `.env` and fill in your Supabase credentials.
    ```bash
    cp .env.example .env
    ```

## Running the Application

### Locally with Uvicorn
To run the server locally for development:
```bash
python3 -m app.main
```
The API will be available at `http://localhost:8000`.
- **Health check**: `http://localhost:8000/health`
- **Interactive API docs**: `http://localhost:8000/docs`

### With Vercel CLI
If you have the Vercel CLI installed:
```bash
vercel dev
```

## Vercel Deployment

This project is configured for Vercel using `vercel.json`.

### What is `vercel.json`?
`vercel.json` is a configuration file that tells Vercel how to handle your project. In this setup:
- **Rewrites**: It redirects all incoming requests (`/(.*)`) to `app/main.py`, which is our FastAPI entry point.
- **Functions**: It specifies that `app/main.py` should be treated as a Python Serverless Function using the `vercel-python` runtime.

This allows FastAPI to run seamlessly as a series of serverless functions on Vercel's infrastructure.
