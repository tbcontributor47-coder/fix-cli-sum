# Fix CLI Sum Tool

You are given a small CLI program inside the container at:

- `/app/sum_cli.py`

The program is supposed to read a text file containing **one integer per line**, compute the sum, and print the result.

Right now, the program is **buggy** and does not correctly handle all valid inputs. There are **multiple bugs** that need to be fixed.

## Your task

Fix `/app/sum_cli.py` so that it meets the requirements below.

## Requirements

1. The CLI must be invoked as:

   ```
   python /app/sum_cli.py <input_file_path>
   ```

   Example:

   ```
   python /app/sum_cli.py /tmp/input.txt
   ```

2. The input file path is the **first positional argument**.

3. The input file contains:

   - One integer per line
   - Lines may have leading/trailing whitespace
   - Blank lines may appear and must be ignored
   - Integers may be negative
   - Empty files are valid (sum = 0)

4. The program must print **exactly** one line to stdout:

   ```
   SUM=<number>
   ```

   Example:

   - If the numbers are `1`, `2`, `-3`, the output must be:

     ```
     SUM=0
     ```

   - For an empty file, the output must be:

     ```
     SUM=0
     ```

5. Exit code:

   - `0` on success
   - Non-zero (e.g., `1`) on error such as file not found

6. Error handling:

   - The program must handle missing files **gracefully**: catch the FileNotFoundError, print an error message to stderr, and exit with a non-zero code (don't let it crash with an unhandled exception)
   - Non-integer lines should be ignored (skip them, don't crash)

## Constraints

- Do not modify the tests.
- Do not change the container environment.
- Only fix the logic in `/app/sum_cli.py`.

## Hints

The current implementation has multiple issues:

- Output format problems
- Edge case handling (empty files, whitespace)
- Missing error handling
- Logic bugs in number parsing
