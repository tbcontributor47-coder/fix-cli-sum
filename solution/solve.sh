#!/usr/bin/env bash
set -euo pipefail

# Oracle solution: fix all bugs in the CLI.
# (Harbor copies this folder to /oracle at runtime.)

cat > /app/sum_cli.py <<'PYTHON'
#!/usr/bin/env python3
"""Fixed CLI: sums integers from a file.

Expected output: SUM=<number>\n
"""

import sys


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python /app/sum_cli.py /app/input.txt", file=sys.stderr)
        return 2

    path = argv[1]
    
    total = 0
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                
                # Ignore blank/whitespace-only lines
                if not s:
                    continue
                
                # Parse and sum all integers (including negative)
                try:
                    total += int(s)
                except ValueError:
                    # Ignore non-integer lines
                    continue
                    
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    # Always print with newline
    print(f"SUM={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
PYTHON

# Sanity check with a test file
echo "1" > /tmp/test_input.txt
echo "2" >> /tmp/test_input.txt
echo "3" >> /tmp/test_input.txt

python /app/sum_cli.py /tmp/test_input.txt
