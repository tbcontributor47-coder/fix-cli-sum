FROM python:3.13-slim-bookworm

WORKDIR /app

# Only copy application files into the image (never tests/ or solution/).
# Note: During build, app/ is one level up from environment/
COPY ../app/ /app/

# Minimal tools; test-only tools (uv/uvx, pytest) install in `tests/test.sh`.
RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /logs/agent /logs/verifier \
  && chmod -R 0777 /logs

# Intentionally run as root for maximum compatibility with portal/CI bind mounts.
