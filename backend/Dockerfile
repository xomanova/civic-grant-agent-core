# FastAPI Backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app.py .

# Copy agent configuration
COPY backend/agent_config.py .
COPY backend/sub_agents ./sub_agents
COPY backend/tools ./tools

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
