FROM ghcr.io/astral-sh/uv:python3.11-alpine

RUN addgroup --gid 32840 -S runner && adduser --uid 32840 -S runner -G runner
USER runner
WORKDIR /home/runner

COPY --link bot/src/ bot/src/
COPY --link bot/pyproject.toml bot/
COPY --link pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked

ENV PYTHONUNBUFFERED=1
STOPSIGNAL SIGINT
ENTRYPOINT ["uv", "run", "--frozen", "--no-sync", "-m", "thesteambot.bot"]
