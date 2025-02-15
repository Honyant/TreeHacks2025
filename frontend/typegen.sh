#!/usr/bin/env bash

# This script generates TypeScript types for the APIs based on OpenAPI specifications.
# Add your commands below to implement the type generation functionality.

bash -c "cd ../backend && ./start.sh"
bun run openapi-typegen || {
  echo "TypeScript types generation failed."
}
bash -c "cd ../backend && ./end.sh"