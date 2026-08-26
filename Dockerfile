FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Entry timestamps are naive local wall-clock strings written by the
# browser, so the server has to keep the household's clock — on UTC it
# reads every entry as hours in the future. Override with -e TZ=... .
ENV TZ=Europe/Vienna
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
VOLUME /app/data
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
