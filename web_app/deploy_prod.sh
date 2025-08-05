#!/usr/bin/env bash
set -euo pipefail

# Use the first argument as TAG (default to “latest”)
TAG=${1:-latest}
export TAG

# Pull the exact images you just pushed
docker compose --env-file .env -f docker_compose_prod.yml pull

# Bring up the services in detached mode
docker compose --env-file .env -f docker_compose_prod.yml up -d
