import re
from contextlib import chdir
from pathlib import Path
from typing import cast

from click.testing import CliRunner


def test_cli_help(tmp_path: Path) -> None:
    from h3a.main import main

    cli_runner = CliRunner()
    with chdir(tmp_path):
        cli_result = cli_runner.invoke(main, ["--help"], prog_name="h3a")

    assert cli_result.exception is None, cli_result.output
    assert cli_result.exit_code == 0, cli_result.output
    assert cli_result.output == (
        "Usage: h3a [OPTIONS]\n"
        "\n"
        "  A simple script for file archiving.\n"
        "\n"
        "Options:\n"
        "  -c, --config FILE            Path to config file.  [default: h3a.yaml]\n"
        "  -e, --encoding TEXT          Encoding of the config file.  [default: utf-8]\n"
        "  -y, --skip-confirm           Skip confirmation prompt.\n"
        "  -t, --threads INTEGER RANGE  Number of threads to use.  [x>=1]\n"
        "  -d, --dry-run                Print plan and exit.\n"
        "  --verbose                    Enable debug logging.\n"
        "  --version                    Show the version and exit.\n"
        "  --help                       Show this message and exit.\n"
    )


def test_cli_simple(tmp_path: Path) -> None:
    from h3a.main import main
    from h3a.plan import Plan, PlanItem

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz" / "blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text("include:\n  - foo.txt\n")

    # -- Execute h3a --
    cli_runner = CliRunner()
    with chdir(tmp_path):
        cli_result = cli_runner.invoke(main, ["-y"], standalone_mode=False)

    # -- Assert cli result --
    assert cli_result.exception is None, cli_result.output
    assert cli_result.exit_code == 0, cli_result.output
    plan = cast(Plan, cli_result.return_value)
    assert isinstance(plan, list)
    assert all(isinstance(plan_item, PlanItem) for plan_item in plan)

    # -- Assert plan content --
    assert len(plan) == 1, plan
    assert plan[0].id == 1
    assert isinstance(plan[0].src, Path)
    assert plan[0].src == (tmp_path / "foo.txt")
    assert isinstance(plan[0].dest, Path)
    assert plan[0].dest.parent == tmp_path
    assert re.fullmatch(r"foo_v\d{8}-\d{6}.txt", plan[0].dest.name)
    assert not plan[0].overwrite_flag

    # -- Assert plan execution --
    assert set(file_path.name for file_path in tmp_path.iterdir()) == {
        "foo.txt",
        "bar.txt",
        "baz",
        "h3a.yaml",
        plan[0].dest.name,
    }
    assert set(file_path.name for file_path in (tmp_path / "baz").iterdir()) == {
        "blah.txt"
    }
    assert plan[0].src.read_text() == plan[0].dest.read_text()
