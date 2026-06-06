CONTRIBUTING: Service & MCP integration

This file documents how to run MCP services locally, install the Remix GitHub App, and guidance for contributors when the project is offered as a paid service.

Local MCP services
- Remix Opus connector:
  - Start: cd mcp-services/remix-opus-connector && python3 server.py
  - Health: http://localhost:3010/health
- Blender MCP:
  - Start: cd mcp-services/blender-mcp && python3 server.py
  - Health: http://localhost:3020/health

GitHub App (Remix Opus connector)
- Use .github/remix-opus-app-manifest.yml to create a GitHub App via the manifest flow:
  - Visit: https://github.com/settings/apps/new/manifest
  - Paste the manifest content and create the app
  - Set webhook URL and private key in app settings
  - Install the app on repositories/orgs

CI notes
- Unit tests run by default in .github/workflows/ci.yml
- Integration tests must be triggered manually via workflow_dispatch with input `run_integration: true`
- Blender MCP depends on the system Blender binary; prefer mocking Blender in CI or run on a self-hosted runner with Blender installed.

Offering as a paid service
- This repo is the codebase. To offer as a service:
  - Create a deployment target (VPS or cloud) for the API and MCP services
  - Package the Remix connector as a deployable service (Docker recommended)
  - Provide an onboarding script to install the GitHub App and configure webhooks/credentials
  - Add a basic pricing & SLA document (not included here)

Docker & container workflow
- Build locally with Docker (from repo root):
  docker build -t remix-opus-connector -f mcp-services/remix-opus-connector/Dockerfile .
- Run locally:
  docker run -d --name remix -p 3010:3010 remix-opus-connector
  curl -sfS http://localhost:3010/health

CI / GitHub Actions
- A workflow (.github/workflows/remix-docker.yml) is provided to build and smoke-test the container via workflow_dispatch.
- To publish the image, extend the workflow with docker/build-push-action and set registry secrets.

If you'd like, Copilot can:
- Add a Dockerfile for the Remix connector
- Add a GitHub Actions workflow to build/publish a Docker image for the Remix connector
- Scaffold a simple pricing & onboarding doc
