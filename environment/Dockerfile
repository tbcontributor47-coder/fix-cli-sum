FROM python:3.11.10-slim

WORKDIR /app

# Only copy application files into the image (never tests/ or solution/).
COPY app/ /app/

# Run as non-root to avoid privileged assumptions.
RUN useradd -m -u 1001 ciuser \
  && chown -R ciuser:ciuser /app \
  # Create expected log directories at build time (image-level),
  # runtime-mounted /logs will be fixed by entrypoint.
  && mkdir -p /logs/agent /logs/verifier \
  && chown -R ciuser:ciuser /logs \
  && chmod -R 0777 /logs

# Copy an entrypoint that will run as root at container start to fix mounted
# /logs ownership, then drop to `ciuser` and exec the requested command.
COPY task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
RUN chmod +x /usr/local/bin/task-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]

USER ciuser
