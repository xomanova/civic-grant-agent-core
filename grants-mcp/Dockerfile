# Grants MCP Server - Cloud Run Sidecar Build
# Based on https://github.com/Tar-ive/grants-mcp.git @ commit 89d667c
#
# This Dockerfile clones the grants-mcp repo at a specific commit and builds
# the MCP-compatible server for Cloud Run deployment as a sidecar container.

# Single stage build - clone and run
FROM python:3.13-slim

# Install runtime dependencies (curl for healthcheck, git for cloning)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Clone the repository at the specific commit
#RUN git clone https://github.com/Tar-ive/grants-mcp.git . && \
#    git checkout 89d667c
# Forked for Auth Header fix to simpler.grants.gov
RUN git clone https://github.com/xomanova/grants-mcp.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables optimized for Cloud Run sidecar
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_TRANSPORT=http \
    LOG_LEVEL=INFO \
    PORT=8081

# Change ownership of app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8081 (sidecar port, different from main backend's 8000)
EXPOSE 8081

# Health check with proper headers for MCP endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f -H "Accept: application/json, text/event-stream" http://localhost:8081/health || exit 1

# Run the MCP-compatible server
CMD ["python", "mcp_compatible_server.py"]
