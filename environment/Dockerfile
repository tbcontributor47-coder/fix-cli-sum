FROM python:3.11.10-slim

WORKDIR /app

# Only copy application files into the image (never tests/ or solution/).
COPY app/ /app/

# Run as non-root to avoid privileged assumptions.
RUN useradd -m -u 1001 ciuser \
  && chown -R ciuser:ciuser /app \
  # Create expected log directories and make them writable by the non-root user
  && mkdir -p /logs/agent /logs/verifier \
  && chown -R ciuser:ciuser /logs \
  && chmod -R 0777 /logs

USER ciuser
