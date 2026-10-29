# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
FROM python:3.12-slim
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    # Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
    PYTHONUNBUFFERED=1 \
    # Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
    APP_ENV=production \
    # Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
    HOST=0.0.0.0
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
WORKDIR /app
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
COPY pyproject.toml README.md ./
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
COPY src ./src
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
RUN pip install --no-cache-dir -e . && useradd --create-home --uid 10001 appuser
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
RUN mkdir -p /app/data && chown -R appuser:appuser /app
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
USER appuser
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
EXPOSE 8000
# Explanation: Docker build instruction: controls how the image is assembled or how the container runs.
CMD ["sh", "-c", "uvicorn mcp_canarytrap.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
