#!/usr/bin/env bash
# Generate TypeScript types from the backend OpenAPI schema.
# Requires: openapi-typescript (npm install -g openapi-typescript)
#
# Usage:
#   cd apps/web && bash scripts/generate-api-types.sh

set -euo pipefail

OPENAPI_JSON="${1:-../../apps/api/openapi.json}"
OUTPUT="${2:-lib/api/generated-types.ts}"

if [ ! -f "$OPENAPI_JSON" ]; then
  echo "ERROR: OpenAPI schema not found at $OPENAPI_JSON"
  echo "Run  poetry run python scripts/generate_openapi.py  first."
  exit 1
fi

npx openapi-typescript "$OPENAPI_JSON" --output "$OUTPUT"
echo "✓ Generated $OUTPUT"
