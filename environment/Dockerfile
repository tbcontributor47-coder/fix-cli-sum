FROM python:3.13-slim-bookworm

WORKDIR /app

# Only copy application files into the image (never tests/ or solution/).
COPY app/ /app/

# Minimal tools + a self-contained verifier runtime.
#
# NOTE: Some evaluators run verifier containers with restricted egress.
# Installing `pytest` + `pytest-json-ctrf` at build time avoids runtime downloads.
RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /logs/agent /logs/verifier \
  && chmod -R 0777 /logs

# Pin verifier deps.
RUN python -m pip install --no-cache-dir \
  pytest==8.4.1 \
  pytest-json-ctrf==0.3.5

# Intentionally run as root for maximum compatibility with portal/CI bind mounts.
