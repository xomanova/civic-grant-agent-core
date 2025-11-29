# Grants MCP Server
# Git submodule from https://github.com/Tar-ive/grants-mcp.git
# Commit: 89d667c

This directory contains the Dockerfile and build configuration for the Grants MCP server,
which runs as a sidecar container to the main backend service on Cloud Run.

## Source Repository
- Repository: https://github.com/Tar-ive/grants-mcp.git
- Commit Hash: 89d667c
- Visit the repository for full documentation on the Grants MCP server.

## Architecture
The grants-mcp server runs as a sidecar container alongside the main civic-grant-agent-backend.
Both containers share the same Cloud Run service instance, allowing localhost communication.

