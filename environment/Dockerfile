FROM python:3.11.10-slim

WORKDIR /app

# Only copy application files into the image (never tests/ or solution/).
COPY app/ /app/

# Run as non-root to avoid privileged assumptions.
RUN useradd -m -u 1001 ciuser \
  && chown -R ciuser:ciuser /app \
  # Create expected log directories at build time (image-level).
  && mkdir -p /logs/agent /logs/verifier \
  && chown -R ciuser:ciuser /logs \
  && chmod -R 0777 /logs

# Run as non-root user by default.
USER ciuser
