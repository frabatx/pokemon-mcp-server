FROM python:3.12-slim

LABEL maintainer="fr.battista@reply.it"
LABEL description="Pokemon Biography MCP Server"

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-dev

COPY src/ ./src/

VOLUME ["/data"]

CMD ["uv", "run", "src/main.py"]