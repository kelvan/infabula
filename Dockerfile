FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Entries are stored as UTC instants; TZ picks which local day and clock
# time they're grouped/shown as. Override with -e TZ=... .
ENV TZ=Europe/Vienna
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra postgres
COPY . .
VOLUME /app/data

# Behind Caddy, so trust its X-Forwarded-Proto — otherwise request.url.scheme
# always reads "http" and the WebAuthn origin check rejects every ceremony.
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips=*"]
