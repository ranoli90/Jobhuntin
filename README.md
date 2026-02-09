# Sorce / JobHuntin

**Sorce** (backend) and **JobHuntin** (frontend) - An automated job application platform powered by AI.

## Project Structure

This monorepo contains the following components:

- **`apps/api/`**: FastAPI backend service.
- **`apps/web/`**: React/Vite frontend application (JobHuntin).
- **`apps/web-admin/`**: React/Vite admin dashboard.
- **`apps/worker/`**: Background worker for processing job applications (Python).
- **`mobile/`**: React Native / Expo mobile app.
- **`packages/`**: Shared Python libraries used by the backend/worker.
- **`infra/supabase/`**: Database schema + migrations.
- **`scripts/`**: Utility and maintenance scripts.

## Repo Map

- [Docs Index](docs/INDEX.md)
- [Reports & Historical Notes](docs/reports/root-docs/INDEX.md)
- [Apps](apps/)
- [Packages](packages/)
- [Infrastructure](infra/)

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
    cd apps/web
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
    cd apps/web
    npm run dev
    ```

## Testing

- **Backend:**
    ```bash
    pytest
    ```
- **Frontend:**
    ```bash
    cd apps/web
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
