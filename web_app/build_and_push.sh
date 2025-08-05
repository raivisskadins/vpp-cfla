#!/usr/bin/env bash
set -euo pipefail

DOCKERHUB_USERNAME=${DOCKERHUB_USERNAME:-"rudis7887"}
TAG=${1:-latest}

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
