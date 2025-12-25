#!/usr/bin/env python3
"""Buggy CLI: sums integers and directives from a file.

Expected output: SUM=<number>\n
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--base", type=int, default=10)
    p.add_argument("--strict", action="store_true")
    p.add_argument("input_file")
    return p.parse_args(argv[1:])


def _strip_separators(token: str) -> str:
    return token.replace("_", "").replace(",", "")


def _parse_int(token: str, base: int) -> int:
    token = _strip_separators(token.strip())
    return int(token, base)


def _sum_range(a: int, b: int) -> int:
    # BUG: off-by-one and naive iteration (too slow for large ranges)
    if a <= b:
        return sum(range(a, b))
    return sum(range(b, a))


def _maybe_strip_inline_comment(s: str) -> str:
    # BUG: strips comments even when '#' has no preceding whitespace
    if "#" in s:
        return s.split("#", 1)[0].rstrip()
    return s


def _read_lines(path: Path) -> list[str]:
    # BUG: does not handle UTF-8 BOM explicitly
    return path.read_text(encoding="utf-8").splitlines()


def _eval_file(
    path: Path,
    *,
    base: int,
    strict: bool,
    seen: set[Path],
) -> int:
    # BUG: includes are resolved relative to CWD, not the including file
    if path in seen:
        raise RuntimeError(f"include cycle detected at: {path}")
    seen.add(path)

    total = 0
    cur_base = base

    for raw in _read_lines(path):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue

        if line.startswith("@"): 
            parts = line.split()
            cmd = parts[0].lower()
            if cmd == "@base" and len(parts) == 2:
                cur_base = int(parts[1])
                continue
            if cmd == "@include" and len(parts) == 2:
                inc = Path(parts[1])
                total += _eval_file(inc, base=cur_base, strict=strict, seen=seen)
                continue
            if cmd == "@range" and len(parts) == 2 and ".." in parts[1]:
                a_s, b_s = parts[1].split("..", 1)
                a = _parse_int(a_s, cur_base)
                b = _parse_int(b_s, cur_base)
                total += _sum_range(a, b)
                continue
            raise ValueError(f"unknown directive: {line}")

        line = _maybe_strip_inline_comment(raw)
        try:
            total += _parse_int(line, cur_base)
        except Exception:
            if strict:
                raise
            continue

    return total


def main(argv: list[str]) -> int:
    try:
        args = _parse_args(argv)
    except SystemExit:
        print("Usage: python /app/sum_cli.py [--base N] [--strict] <input_file_path>", file=sys.stderr)
        return 2

    if not (2 <= args.base <= 36):
        print("Error: --base must be in the range 2..36", file=sys.stderr)
        return 2

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        total = _eval_file(input_path, base=args.base, strict=args.strict, seen=set())
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    print(f"SUM={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
