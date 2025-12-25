import os
import subprocess
from pathlib import Path


def run_sum_cli(
    input_path: Path,
    *,
    base: int | None = None,
    strict: bool = False,
) -> tuple[int, str, str]:
    cmd: list[str] = ["python", "/app/sum_cli.py"]
    if base is not None:
        cmd.extend(["--base", str(base)])
    if strict:
        cmd.append("--strict")
    cmd.append(str(input_path))

    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def run_sum_cli_raw(args: list[str]) -> tuple[int, str, str]:
    cmd: list[str] = ["python", "/app/sum_cli.py", *args]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_basic_numbers_and_comments() -> None:
    p = write_text(
        Path("/tmp/input.txt"),
        """
        # comment line
        1
          2   # inline comment
        -3
        not_a_number
        4#not_inline_comment (invalid token, ignored in non-strict)
        """.lstrip(),
    )
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=0\n"


def test_strict_mode_rejects_invalid_data_line() -> None:
    p = write_text(Path("/tmp/strict.txt"), "1\n2\n4#bad\n")
    code, out, err = run_sum_cli(p, strict=True)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_utf8_bom_is_accepted() -> None:
    # BOM at start of file should not break parsing.
    p = Path("/tmp/bom.txt")
    p.write_bytes(("\ufeff1\n2\n").encode("utf-8"))
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=3\n"


def test_separators_and_plus_sign() -> None:
    p = write_text(Path("/tmp/seps.txt"), "+1_000\n2,000\n")
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=3000\n"


def test_base_directive_switching() -> None:
    p = write_text(Path("/tmp/base.txt"), "@base 16\nff\n@base 10\n10\n")
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=265\n"


def test_cli_base_overrides_default_parsing_base() -> None:
    p = write_text(Path("/tmp/cli_base.txt"), "ff\n")
    code, out, err = run_sum_cli(p, base=16)
    assert code == 0, err
    assert out == "SUM=255\n"


def test_cli_base_validation_requires_2_to_36() -> None:
    p = write_text(Path("/tmp/base_invalid_cli.txt"), "1\n")
    code, out, err = run_sum_cli(p, base=1)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err

    code, out, err = run_sum_cli(p, base=37)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_range_directive_large_and_reversed() -> None:
    # 1..100000000 => n(n+1)/2 = 5_000_000_050_000_000
    p = write_text(
        Path("/tmp/range.txt"),
        "@range 1..100000000\n@range 5..3\n",
    )
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=5000000050000012\n"  # 5_000_000_050_000_000 + 12


def test_directives_malformed_or_unknown_are_errors() -> None:
    p = write_text(
        Path("/tmp/bad_directives.txt"),
        "@unknown 1\n1\n",
    )
    code, out, err = run_sum_cli(p)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err

    p = write_text(Path("/tmp/bad_directives2.txt"), "@base\n")
    code, out, err = run_sum_cli(p)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err

    p = write_text(Path("/tmp/bad_directives3.txt"), "@base 1\n")
    code, out, err = run_sum_cli(p)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_include_relative_to_including_file() -> None:
    root = Path("/tmp/include")
    main = write_text(
        root / "main.txt",
        "@include sub/nums.txt\n@range 1..3\n",
    )
    write_text(root / "sub" / "nums.txt", "@base 16\n0a\n")

    code, out, err = run_sum_cli(main)
    assert code == 0, err
    # sub contributes 0x0a=10, range contributes 6
    assert out == "SUM=16\n"


def test_missing_input_file_is_graceful() -> None:
    missing = Path("/tmp/does_not_exist_12345.txt")
    if missing.exists():
        os.remove(missing)
    code, out, err = run_sum_cli(missing)
    assert code == 1
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_missing_include_file_is_graceful() -> None:
    root = Path("/tmp/missing_include")
    main = write_text(root / "main.txt", "@include sub/missing.txt\n1\n")
    code, out, err = run_sum_cli(main)
    assert code == 1
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_include_cycle_is_detected() -> None:
    root = Path("/tmp/cycle")
    a = write_text(root / "a.txt", "@include b.txt\n1\n")
    write_text(root / "b.txt", "@include a.txt\n2\n")
    code, out, err = run_sum_cli(a)
    assert code == 1
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_usage_error_missing_positional_input_file() -> None:
    code, out, err = run_sum_cli_raw([])
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err
