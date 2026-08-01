# agents.md

## Project Context
This is a Django web application that uses OpenSearch as its primary data backend instead of a relational database.

## Working Principles
- Keep changes small and focused.
- Prefer explicit, readable code over clever abstractions.
- Do not invent components that do not exist in the repository.
- Preserve the existing architecture and project structure.
- Treat OpenSearch mappings and indexing behavior as part of the application contract.

## Tech Stack
- Django
- OpenSearch
- uv for dependency management and execution
- Docker where applicable

## Development Notes
- Use `uv sync` to install dependencies.
- Use `uv run` to execute project commands.
- Keep dependency changes in `pyproject.toml` and `uv.lock`.
- Respect the separation between Django logic and OpenSearch access.
- Consider documentation.
- After every modification run unit tests.
- After every modification run application, access all known pages and test error pages.

## Running the Application
- Use `uv run python manage.py runserver` to start the development server.
- The application will be available at `http://127.0.0.1:8000`.

## Running Tests
- Use `uv run python manage.py test` to run the test suite.

## Documentation
- Update documentation when behavior or structure changes.
- Keep README and architecture notes consistent with the codebase.
- Use concise and practical wording.
- Add and keep docstrings up-to-date with every code change.

## Agent Behavior
- Make minimal, safe edits.
- Follow existing conventions in the repository.
- Prefer implementation details that match the current codebase over assumptions.
