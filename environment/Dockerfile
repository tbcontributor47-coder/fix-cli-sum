FROM python:3.13-slim-bookworm

WORKDIR /app

# Only copy application files into the image (never tests/ or solution/).
COPY app/ /app/

# Minimal tools + uv/uvx pinned install.
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl \
  && rm -rf /var/lib/apt/lists/* \
  && curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh \
  && ln -sf /root/.local/bin/uv /usr/local/bin/uv \
  && ln -sf /root/.local/bin/uvx /usr/local/bin/uvx \
  && mkdir -p /logs/agent /logs/verifier \
  && chmod -R 0777 /logs

# Intentionally run as root for maximum compatibility with portal/CI bind mounts.
