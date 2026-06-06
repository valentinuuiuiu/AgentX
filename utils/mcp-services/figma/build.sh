#!/usr/bin/env bash
# Build figma MCP Server Docker image

set -euo pipefail

TAG=${1:-figma}

echo "Building figma MCP Server Docker image with tag: ${TAG}..."

docker build -t "${TAG}" .

echo "Built ${TAG} successfully!"
echo "Run with: docker run -p 3110:3110 ${TAG}"
