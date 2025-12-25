# Fix CLI Sum Tool (v2)

You are given a small CLI program inside the container at:

- `/app/sum_cli.py`

The program reads a text file containing a mixture of **numbers** and **directives**, computes a total, and prints the result.

Right now, the program is **buggy** and does not correctly implement the required parsing and directives. Fix it.

## Your task

Fix `/app/sum_cli.py` so that it meets the requirements below.

## CLI

The CLI must be invoked as:

```
python /app/sum_cli.py [--base N] [--strict] <input_file_path>
```

- `<input_file_path>` is required.
- `--base N` sets the default numeric base (integer $2 \le N \le 36$). Default: `10`.
- `--strict` enables strict parsing: invalid data lines become errors (see below).

## Input format

The input file is UTF-8 text. It may begin with a UTF-8 BOM.

Each line (after trimming leading/trailing whitespace) is one of:

1. **Blank line**: ignored.
2. **Comment line**: ignored if the trimmed line starts with `#`.
3. **Directive line**: trimmed line starts with `@`.
4. **Data line**: everything else.

### Data lines

Data lines contribute either 0 (ignored) or a parsed integer value.

- A data line may contain an **inline comment** introduced by `#`, but only when `#` is preceded by at least one whitespace character.
  - Example (valid): `123   # hello`
  - Example (invalid token): `123#hello` (no whitespace before `#`)
- The numeric token supports:
  - Optional leading `+` or `-`
   - Base-dependent digits (ASCII `0-9`, `A-Z`, case-insensitive). Non-ASCII numerals (e.g., `١`) are invalid.
  - Optional visual separators `_` and `,` anywhere in the token (they are ignored)

If a data line cannot be parsed into an integer:

- **Non-strict mode (default):** ignore that line.
- **Strict mode (`--strict`):** treat it as an error (exit non-zero).

### Directives

Directives are always significant; malformed or unknown directives are errors.

Supported directives:

1. `@base N`
   - Sets the *current* base for subsequent number parsing.
   - `N` must be in the range $2..36$.

2. `@range A..B`
   - Adds the sum of **all integers from A to B inclusive**.
   - `A` and `B` are parsed using the *current* base and the same token rules as data lines.
   - `A` may be greater than `B` (it still sums the inclusive range).
   - Ranges may be very large; your implementation must not iterate over every integer in the range.

3. `@include PATH`
   - Reads and processes another file, then continues processing the current file.
   - Relative paths are resolved relative to the including file's directory.
   - Include cycles must be detected and treated as an error.

## Output

On success, print **exactly one line** to stdout:

```
SUM=<number>
```

The output must end with a newline.

## Exit codes / error handling

- Exit `0` on success.
- Exit `2` for usage errors or parse errors (including strict-mode data-line errors and malformed directives).
- Exit `1` for file I/O errors (missing input file, missing include file, include cycle).

On any error:

- Print a human-readable error message to stderr.
- Do not print a Python traceback.

## Constraints

- Do not modify the tests.
- Do not change the container environment.
- Only fix the logic in `/app/sum_cli.py`.

