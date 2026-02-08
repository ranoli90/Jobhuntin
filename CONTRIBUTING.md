# Contributing to Sorce

We welcome contributions to the Sorce/JobHuntin platform! Please follow these guidelines to ensure a smooth collaboration process.

## Code of Conduct

*   Be respectful and inclusive.
*   Focus on constructive feedback.
*   Report any issues to the project maintainers.

## Development Workflow

1.  **Branching:**
    *   `main`: Production-ready code.
    *   `dev`: Integration branch for ongoing development.
    *   Feature branches: `feature/your-feature-name` (created from `dev`).
    *   Fix branches: `fix/issue-description` (created from `dev` or `main` for hotfixes).

2.  **Commits:**
    *   Use clear and descriptive commit messages.
    *   Follow the format: `type(scope): description`.
        *   Examples: `feat(api): add new user endpoint`, `fix(web): correct pricing toggle`.

3.  **Pull Requests:**
    *   Push your branch to the repository.
    *   Open a Pull Request (PR) against `dev`.
    *   Provide a clear description of the changes and the problem solved.
    *   Ensure all tests pass before requesting review.

## Coding Standards

### Python (Backend)
*   We use **Ruff** for linting and formatting.
*   Follow PEP 8 guidelines.
*   Type hints are required (checked by **Mypy**).
*   Run checks before committing:
    ```bash
    ruff check .
    mypy .
    ```

### TypeScript/React (Frontend)
*   Use functional components and hooks.
*   Ensure strict type safety with TypeScript.
*   Follow the existing file structure in `web/src`.

## Testing

*   **Backend:** Write unit tests using `pytest` for new logic.
*   **Frontend:** Ensure components render correctly and critical flows are tested.

## Reporting Issues

*   Check existing issues before creating a new one.
*   Provide reproduction steps and environment details.

Thank you for contributing!
