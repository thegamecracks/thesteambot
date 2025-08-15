FROM python:3.11-alpine AS project-build

COPY --link src/ src/
COPY --link pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache \
    pip wheel --wheel-dir wheelhouse .

FROM python:3.11-alpine AS project

COPY --from=project-build wheelhouse/ wheelhouse/

# --no-build-isolation to avoid re-installing setuptools in pyproject.toml
# --no-index to avoid network resolution
RUN pip install --no-build-isolation --no-index wheelhouse/* \
    && rm -r wheelhouse/

RUN addgroup --gid 32841 -S runner && adduser --uid 32841 -S runner -G runner
USER runner
WORKDIR /home/runner

STOPSIGNAL SIGINT
ENTRYPOINT ["python", "-u", "-m", "thesteambot.web"]
