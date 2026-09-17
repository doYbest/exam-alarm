FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8000
