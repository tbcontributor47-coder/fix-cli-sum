#!/usr/bin/env python3
"""Buggy CLI: sums integers from a file.

Expected output: SUM=<number>\n
"""

import sys


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python /app/sum_cli.py /app/input.txt", file=sys.stderr)
        return 2

    path = argv[1]
    
    # BUG 1: No error handling for missing file - will crash with FileNotFoundError
    
    total = 0
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
        # BUG 2: Empty file handling - prints wrong format
        if len(lines) == 0:
            print("SUM=")  # Missing 0
            return 0
            
        for line in lines:
            s = line.strip()
            
            if not s:
                continue

            # BUG 3: This incorrectly ignores negative numbers
            if s.startswith("-"):
                continue
            
            # BUG 4: No error handling for non-integer values
            # If line contains "abc" or "12.5", int() will crash
            total += int(s)

    # BUG 5: Missing newline in output (should end with \n)
    print(f"SUM={total}", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
