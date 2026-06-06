#!/usr/bin/env bash
# Deploy figma MCP Server

set -euo pipefail

IMAGE=${1:-}
PORT=${PORT:-3110}

if [ -n "$IMAGE" ]; then
  echo "Deploying figma MCP Server using image: $IMAGE"
  docker pull "$IMAGE"
  docker stop figma || true
  docker rm figma || true
  docker run -d --name figma -p ${PORT}:3110 --restart unless-stopped -e PORT=3110 -e REGISTRY_URL=${REGISTRY_URL:-http://mcp-registry:3001} "$IMAGE"
else
  echo "No image provided. Building and deploying with docker-compose (local build)."
  ./build.sh
  docker-compose up -d
fi

echo "figma MCP Server deployed!"
echo "Access at: http://localhost:${PORT}"
echo "Health check: http://localhost:${PORT}/health"
