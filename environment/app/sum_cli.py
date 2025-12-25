#!/usr/bin/env python3
"""Fixed CLI: sums integers and directives from a file.

Expected output: SUM=<number>\n
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


USAGE = "python /app/sum_cli.py [--base N] [--strict] <input_file_path>"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--base", type=int, default=10)
    p.add_argument("--strict", action="store_true")
    p.add_argument("input_file", nargs="?")
    args = p.parse_args(argv[1:])
    if args.input_file is None:
        raise ValueError("missing input_file")
    return args


def _strip_utf8_bom(s: str) -> str:
    if s.startswith("\ufeff"):
        return s.lstrip("\ufeff")
    return s


def _strip_separators(token: str) -> str:
    return token.replace("_", "").replace(",", "")


def _split_inline_comment(raw_line: str) -> str:
    # Inline comment only starts at '#' when preceded by whitespace.
    for i, ch in enumerate(raw_line):
        if ch != "#":
            continue
        if i == 0:
            return ""  # whole-line comment handled elsewhere; keep consistent
        if raw_line[i - 1].isspace():
            return raw_line[:i]
    return raw_line


def _parse_int_token(token: str, base: int) -> int:
    t = _strip_separators(token.strip())
    if not t:
        raise ValueError("empty integer token")
    return int(t, base)


def _sum_inclusive_range(a: int, b: int) -> int:
    # Sum of integers in [lo, hi] inclusive.
    lo, hi = (a, b) if a <= b else (b, a)
    n = hi - lo + 1
    return n * (lo + hi) // 2


def _read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = _strip_utf8_bom(text)
    return text.splitlines()


def _eval_file(
    path: Path,
    *,
    base: int,
    strict: bool,
    stack: list[Path],
) -> int:
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    if resolved in stack:
        cycle = " -> ".join(str(p) for p in (stack + [resolved]))
        raise IncludeCycleError(f"include cycle detected: {cycle}")

    stack.append(resolved)
    try:
        total = 0
        cur_base = base

        for raw in _read_lines(path):
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue

            if stripped.startswith("@"):
                # Directives are errors if malformed.
                parts = stripped.split(maxsplit=1)
                cmd = parts[0].lower()

                if cmd == "@base":
                    if len(parts) != 2:
                        raise ParseError("@base requires an argument")
                    try:
                        new_base = int(parts[1].strip(), 10)
                    except Exception:
                        raise ParseError("@base argument must be an integer")
                    if not (2 <= new_base <= 36):
                        raise ParseError("@base must be in the range 2..36")
                    cur_base = new_base
                    continue

                if cmd == "@include":
                    if len(parts) != 2:
                        raise ParseError("@include requires a path")
                    inc_text = parts[1].strip()
                    if not inc_text:
                        raise ParseError("@include requires a non-empty path")
                    inc_path = Path(inc_text)
                    if not inc_path.is_absolute():
                        inc_path = (path.parent / inc_path)
                    if not inc_path.exists():
                        raise IncludeIOError(f"include file not found: {inc_path}")
                    total += _eval_file(inc_path, base=cur_base, strict=strict, stack=stack)
                    continue

                if cmd == "@range":
                    if len(parts) != 2:
                        raise ParseError("@range requires A..B")
                    spec = parts[1].strip()
                    if ".." not in spec:
                        raise ParseError("@range must be of the form A..B")
                    a_s, b_s = spec.split("..", 1)
                    a = _parse_int_token(a_s, cur_base)
                    b = _parse_int_token(b_s, cur_base)
                    total += _sum_inclusive_range(a, b)
                    continue

                raise ParseError(f"unknown directive: {cmd}")

            # Data line
            data = _split_inline_comment(raw)
            data = data.strip()
            if not data:
                continue

            try:
                total += _parse_int_token(data, cur_base)
            except Exception:
                if strict:
                    raise ParseError(f"invalid integer token: {data!r}")
                continue

        return total
    finally:
        stack.pop()


class ParseError(Exception):
    pass


class IncludeIOError(Exception):
    pass


class IncludeCycleError(Exception):
    pass


def main(argv: list[str]) -> int:
    try:
        args = _parse_args(argv)
    except Exception:
        print(f"Usage: {USAGE}", file=sys.stderr)
        return 2

    if not (2 <= args.base <= 36):
        print("Error: --base must be in the range 2..36", file=sys.stderr)
        return 2

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        total = _eval_file(input_path, base=args.base, strict=args.strict, stack=[])
    except IncludeCycleError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IncludeIOError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"SUM={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
