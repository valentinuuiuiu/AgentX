# GitHub Copilot instructions for clean_rehoboam_project

This file gives Copilot-specific guidance for running, testing, and interacting with the repository so assistant sessions are fast, safe, and predictable.

## Quick build / dev commands

- Frontend (Vite React):
  - Install: npm install
  - Start dev server: npm run dev (serves at http://localhost:5001)
  - Build for production: npm run build
  - Run a single Jest test file:
    - npx jest <path/to/test-file>  # e.g. npx jest src/application/__tests__/priceService.test.ts
    - or: npm test -- <path/to/test-file>

- Backend (Python / FastAPI):
  - Create venv: python3 -m venv .venv && source .venv/bin/activate
  - Install deps: pip install -r requirements.txt
  - Copy env: cp .env.example .env && edit .env
  - Start local API (dev): uvicorn api_server:app --reload --host 0.0.0.0 --port 5002

- MCP services (examples):
  - Blender MCP: python3 mcp-services/blender-mcp/server.py (service: http://localhost:3020)
  - Remix Opus connector: python3 mcp-services/remix-opus-connector/server.py (service: http://localhost:3010)

## Tests (recommended defaults for Copilot sessions)

Observations from recent interactive runs: running the entire Python test suite is slow and can hang because the repo contains a large, mixed test directory and local venvs. Default Copilot behavior should therefore avoid running full pytest.

Recommended default test workflow for assistants:

1. Run JS tests first (fast): npm test (or run a single test with npx jest <path>)
2. Run targeted Python tests only (fast subset):
   - Run a single file: python -m pytest -q tests/test_api_integration.py
   - Run all project tests in tests/ (when needed): python -m pytest -q tests/
   - Run by keyword: pytest -k "PriceService or small_unit_test"
   - Avoid running pytest at repository root (do not let pytest autodiscover packages in virtualenvs). Explicitly pass the tests/ directory or a file path.
3. When exploratory/debugging runs are needed, use a timeout or stop-on-first-fail:
   - timeout 300s python -m pytest tests/test_file.py
   - pytest -x (stop on first fail)

If heavy/integration coverage is required, run those tests separately (see below for marking guidance).

## Key architecture (high level)

- Frontend: src/ (React + Vite). Tests live under src/application/__tests__.
- Backend/API: api_server.py (FastAPI). Core Python modules live at project root and utils/.
- MCP services: mcp-services/ contains small local HTTP services (Blender, Remix connectors).
- Tests: tests/ contains Python test suites; some are large/integration/fuzzing tests.
- Smart contracts: contracts/ (Hardhat config present)

## Key conventions and project-specific patterns

- Environment: copy .env.example to .env and fill ALCHEMY_API_KEY, OPENAI_API_KEY, ETHERSCAN_API_KEY, etc.
- Ports commonly used in local dev:
  - Frontend: 5001
  - Backend API: 5002
  - Remix MCP: 3010
  - Blender MCP: 3020
- Prefer explicit commands over discovery. Example: "python -m pytest tests/test_api_integration.py" rather than "pytest".
- Virtualenvs may be present in the workspace (babyagi_venv, signal_venv). Avoid allowing test discovery to scan site-packages or venvs: always pass an explicit tests path.

## Guidance for marking heavy/integration tests (suggested to add to repo)

- Add pytest markers (unit, integration, heavy) and a pytest.ini to separate runs:

  [pytest]
  markers =
    integration: slow integration tests
    heavy: resource-intensive or long-running

- Example run commands:
  - Unit-only: pytest -m "not integration and not heavy" -q
  - Integration-only: pytest -m integration -q

## Session insights and why these rules exist

- Previous assistant sessions attempted to run the full Python suite and experienced long runs or timeouts because:
  - tests/ contains heavy and fuzzing tests
  - local virtualenvs (babyagi_venv, signal_venv) make autodiscovery expensive and sometimes include third-party package tests
- These instructions bias Copilot toward fast, targeted commands and explicit test paths to minimize wasted time during interactive debugging.

## When to run the full suite

- Full pytest runs should be reserved for CI or dedicated long-running verification on a clean CI worker. When running locally, run targeted suites or apply timeouts.

---

If you'd like, Copilot can also:
- Add a pytest.ini and example GitHub Actions job that separates unit vs integration runs.
- Add a short CONTRIBUTING subsection describing how to label tests as integration/heavy.

MCP services configuration (requested):
- Remix Opus connector (localhost:3010):
  - Dev start: cd mcp-services/remix-opus-connector && python3 server.py
  - Health endpoint: http://localhost:3010/health
  - CI note: these services are optional for unit test runs; if CI needs them, run them in separate service containers or mock their endpoints.

- Blender MCP (localhost:3020):
  - Dev start: cd mcp-services/blender-mcp && python3 server.py
  - Health endpoint: http://localhost:3020/health
  - CI note: Blender MCP may depend on system Blender binary; prefer mocking during CI or run on a dedicated runner with Blender installed.

Would you like Copilot to (choose any):
1) create this file now (done),
2) also add pytest.ini and CI job,
3) add example scripts to package.json/Makefile to run targeted tests?

