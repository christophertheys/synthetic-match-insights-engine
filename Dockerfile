FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md LICENSE ./
COPY matchbrain ./matchbrain
COPY data ./data
COPY docs ./docs
COPY --from=web /web/dist ./web/dist
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["python", "-m", "matchbrain"]
