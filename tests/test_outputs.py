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


def test_base_switch_midfile() -> None:
    # Decimal 10, then switch to base-16 where 'A' == 10, then '1'
    p = write_text(Path("/tmp/base_switch.txt"), "10\n@base 16\nA\n1\n")
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=21\n"


def test_boundary_bases_2_and_36() -> None:
    # Ensure directive base 2 and base 36 are accepted and applied at the right positions
    p = write_text(Path("/tmp/bases_2_36.txt"), "@base 2\n1\n@base 36\nz\n")
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    # 1 (base 2) + z (base 36 == 35) == 36
    assert out == "SUM=36\n"


def test_unicode_digits_are_invalid_in_non_strict_mode() -> None:
    # Spec restricts digits to ASCII 0-9 and A-Z. Non-ASCII numerals are invalid tokens.
    # In non-strict mode, invalid data lines are ignored.
    p = write_text(Path("/tmp/unicode_digits.txt"), "١\n")  # U+0661
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=0\n"


def test_unicode_digits_are_errors_in_strict_mode() -> None:
    p = write_text(Path("/tmp/unicode_digits_strict.txt"), "١\n")  # U+0661
    code, out, err = run_sum_cli(p, strict=True)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_range_endpoints_use_current_base() -> None:
    # Ensure @range endpoints are parsed using the current base (not always base-10).
    # In base 16: a..f == 10..15, sum = 75.
    p = write_text(Path("/tmp/range_base16.txt"), "@base 16\n@range a..f\n")
    code, out, err = run_sum_cli(p)
    assert code == 0, err
    assert out == "SUM=75\n"


def test_include_malformed_arguments_are_errors() -> None:
    # Malformed directives are errors.
    p = write_text(Path("/tmp/include_no_arg.txt"), "@include\n")
    code, out, err = run_sum_cli(p)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err

    p = write_text(Path("/tmp/include_empty_arg.txt"), "@include    \n")
    code, out, err = run_sum_cli(p)
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert "Traceback" not in err


def test_combined_tricky_case_includes_and_mixed() -> None:
    # A combined case that mixes an included file, an internal @base switch,
    # separators and a hex region afterwards. This forces correct include resolution
    # and ordered application of @base directives.
    root = Path("/tmp/tricky_case")
    main = write_text(
        root / "main.txt",
        "@include parts/p1.txt\n@base 16\nF\n1_0\n",
    )
    # parts/p1.txt: 2, +3, then switch to base 10 and a '4'
    write_text(root / "parts" / "p1.txt", "2\n+3\n@base 10\n4\n")

    code, out, err = run_sum_cli(main)
    assert code == 0, err
    # parts/p1 contributes 2 + 3 + 4 = 9, then main has F (hex=15) and 1_0 (hex 16) => 9 + 15 + 16 = 40
    assert out == "SUM=40\n"
