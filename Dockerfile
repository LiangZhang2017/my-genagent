# ----------------------------
# Stage 1: Build the React UI
# ----------------------------
FROM node:20-alpine AS ui
WORKDIR /app/ui
COPY ./ui/ ./
RUN npm ci && npm run build    # outputs build into ../ui-dist (i.e., /app/ui-dist)

# ----------------------------
# Stage 2: Build the backend
# ----------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_NAME="MyGenAgent" \
    AGENT_VERSION="v1.0.0" \
    FRONTEND_DIR="/srv/ui-dist"

WORKDIR /srv

# Install backend deps
COPY ./backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend + manifest
COPY ./backend ./backend
COPY ./agent.manifest.json ./

# Copy the built UI from stage 1
COPY --from=ui /app/ui-dist ./ui-dist

EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]