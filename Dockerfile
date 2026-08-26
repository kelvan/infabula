FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Entries are stored as UTC instants; TZ picks which local day and clock
# time they're grouped/shown as. Override with -e TZ=... .
ENV TZ=Europe/Vienna
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
VOLUME /app/data
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
