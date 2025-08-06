#!/usr/bin/env bash
set -euo pipefail

# Ensure we have the necessary credentials
DOCKERHUB_USERNAME=${DOCKERHUB_USERNAME:-}
if [[ -z "$DOCKERHUB_USERNAME" ]]; then
  echo "Error: DOCKERHUB_USERNAME is not set. Please add it to your .env."
  exit 1
fi

DOCKERHUB_TOKEN=${DOCKERHUB_TOKEN:-}
if [[ -z "$DOCKERHUB_TOKEN" ]]; then
  echo "Error: DOCKERHUB_TOKEN is not set. Please add your Docker Hub access token to .env."
  exit 1
fi

# Tag to use (first arg, fallback to TAG in .env, then to 'latest')
TAG=${1:-${TAG:-latest}}

echo "→ Logging in to Docker Hub as $DOCKERHUB_USERNAME…"
echo "$DOCKERHUB_TOKEN" | docker login \
  --username "$DOCKERHUB_USERNAME" \
  --password-stdin

echo "→ Building backend image…"
docker build \
  -t "${DOCKERHUB_USERNAME}/web-backend:${TAG}" \
  -f web_app/backend/Dockerfile \
  web_app/backend

echo "→ Building frontend image…"
docker build \
  -t "${DOCKERHUB_USERNAME}/web-frontend:${TAG}" \
  -f web_app/frontend/Dockerfile \
  web_app/frontend

echo "→ Pushing images to Docker Hub…"
docker push "${DOCKERHUB_USERNAME}/web-backend:${TAG}"
docker push "${DOCKERHUB_USERNAME}/web-frontend:${TAG}"

echo "✓ Built & pushed both images as :${TAG}"
