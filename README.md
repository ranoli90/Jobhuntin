# Sorce / JobHuntin

**Sorce** (backend) and **JobHuntin** (frontend) - An automated job application platform powered by AI.

## Project Structure

This monorepo contains the following components:

- **`api/`**: FastAPI backend service.
- **`web/`**: React/Vite frontend application (JobHuntin).
- **`web-admin/`**: React/Vite admin dashboard.
- **`worker/`**: Background worker for processing job applications (Python).
- **`mobile/`**: React Native / Expo mobile app.
- **`shared/`**: Shared Python logic and utilities.
- **`supabase/`**: Database migrations and configuration.
- **`scripts/`**: Utility and maintenance scripts.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Supabase CLI (optional, for local DB)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd sorce
    ```

2.  **Backend Setup:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

3.  **Frontend Setup:**
    ```bash
    cd web
    npm install
    ```

### Running Locally

1.  **Start the Database:**
    Ensure you have a local Postgres instance or a Supabase project connected.
    Copy `.env.example` to `.env` and fill in the values.

2.  **Run the Backend:**
    ```bash
    uvicorn api.main:app --reload
    ```

3.  **Run the Frontend:**
    ```bash
    cd web
    npm run dev
    ```

## Testing

- **Backend:**
    ```bash
    pytest
    ```
- **Frontend:**
    ```bash
    cd web
    npm test
    ```

## Deployment

The project is configured for deployment on Render (`render.yaml`).
Database migrations are managed via Supabase.

## Documentation

See the `docs/` directory for detailed documentation:
- [Playbooks](docs/playbooks/)
- [Strategy](docs/strategy/)

## License

Proprietary. All rights reserved.
