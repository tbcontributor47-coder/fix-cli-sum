#!/usr/bin/env sh
set -eu

# Entrypoint to ensure /logs is writable by the non-root ciuser.
# Runs as root at container start, fixes ownership/permissions on /logs,
# then drops privileges to `ciuser` to run the requested command.

mkdir -p /logs/agent /logs/verifier

# Try to chown the mounted path to ciuser (uid 1001) if possible; ignore failures.
chown -R ciuser:ciuser /logs 2>/dev/null || true
chmod -R 0777 /logs 2>/dev/null || true

if [ "$(id -u)" -eq 0 ]; then
  # If no command given, drop to an interactive shell as ciuser
  if [ "$#" -eq 0 ]; then
    exec su -s /bin/sh ciuser -c "sh"
  fi
  # Concatenate args for su -c
  CMD="$*"
  exec su -s /bin/sh ciuser -c "$CMD"
else
  exec "$@"
fi
