# Use a small official Python image for repeatable demonstration environments.
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]"
EXPOSE 8000
CMD ["python", "-m", "mcp_canarytrap.api"]
