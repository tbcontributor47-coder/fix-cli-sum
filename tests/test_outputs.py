import subprocess
from pathlib import Path


def run_sum_cli(input_text: str) -> tuple[int, str, str]:
    p = Path("/tmp/input.txt")
    p.write_text(input_text, encoding="utf-8")

    proc = subprocess.run(
        ["python", "/app/sum_cli.py", str(p)],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_sum_cli_on_missing_file() -> tuple[int, str, str]:
    proc = subprocess.run(
        ["python", "/app/sum_cli.py", "/tmp/does_not_exist_12345.txt"],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


# Level 1: Basic functionality
def test_sums_integers_including_negative_and_blanks() -> None:
    """Sums integers, ignoring blanks, and handles negatives."""
    code, out, err = run_sum_cli("1\n 2\n\n-3\n")
    assert code == 0, err
    assert out == "SUM=0\n"


def test_all_negative() -> None:
    """Handles an input containing only negative integers."""
    code, out, err = run_sum_cli("-1\n-2\n")
    assert code == 0, err
    assert out == "SUM=-3\n"


# Level 2: Edge cases
def test_whitespace_only_lines_ignored() -> None:
    """Ignores lines that contain only whitespace characters."""
    code, out, err = run_sum_cli("  \n\t\n5\n")
    assert code == 0, err
    assert out == "SUM=5\n"


def test_empty_file() -> None:
    """Empty files are valid and sum to 0."""
    code, out, err = run_sum_cli("")
    assert code == 0, err
    assert out == "SUM=0\n"


def test_single_number() -> None:
    """Single-line input prints the same number as the sum."""
    code, out, err = run_sum_cli("42\n")
    assert code == 0, err
    assert out == "SUM=42\n"


# Level 3: Large numbers and mixed whitespace
def test_large_numbers() -> None:
    """Handles large magnitude integers without overflow-related issues."""
    code, out, err = run_sum_cli("1000000\n-1000000\n5\n")
    assert code == 0, err
    assert out == "SUM=5\n"


def test_mixed_whitespace() -> None:
    """Trims mixed leading/trailing whitespace around integers."""
    code, out, err = run_sum_cli("  10  \n\t20\t\n\n\n30\n")
    assert code == 0, err
    assert out == "SUM=60\n"


def test_zero_sum() -> None:
    """Correctly prints SUM=0 when the arithmetic sum is zero."""
    code, out, err = run_sum_cli("0\n0\n0\n")
    assert code == 0, err
    assert out == "SUM=0\n"


# Level 4: Error handling
def test_missing_file_non_zero_exit() -> None:
    """Missing input path should return a non-zero exit code."""
    code, out, err = run_sum_cli_on_missing_file()
    assert code != 0, "Should return non-zero exit code for missing file"


def test_ignores_non_integer_lines() -> None:
    """Skips non-integer lines instead of crashing or failing."""
    code, out, err = run_sum_cli("5\nabc\n10\n12.5\nxyz\n3\n")
    assert code == 0, err
    assert out == "SUM=18\n", "Should sum valid integers (5+10+3) and skip non-integers"
