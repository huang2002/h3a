import re
from contextlib import chdir
from pathlib import Path
from subprocess import run

from click.testing import CliRunner
from pytest import TempPathFactory

TIMESTAMP_PATTERN = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\]"


def test_cli_help() -> None:
    process = run(["h3a", "--help"], check=True, capture_output=True, text=True)
    assert process.stdout == (
        "Usage: h3a [OPTIONS]\n"
        "\n"
        "  A simple script for file archiving.\n"
        "\n"
        "Options:\n"
        "  -c, --config FILE            Path to config file.  [default: h3a.yaml]\n"
        "  -e, --encoding TEXT          Encoding of the config file.  [default: utf-8]\n"
        "  --help-config                Show config schema and exit.\n"
        "  -y, --skip-confirm           Skip confirmation prompt.\n"
        "  -t, --threads INTEGER RANGE  Number of threads to use.  [x>=1]\n"
        "  --dry-run                    Print plan and exit.\n"
        "  --verbose                    Enable info-level logging.\n"
        "  --debug                      Enable debug-level logging.\n"
        "  --version                    Show the version and exit.\n"
        "  --help                       Show this message and exit.\n"
    )


def test_cli_help_config() -> None:
    process = run(["h3a", "--help-config"], check=True, capture_output=True, text=True)
    assert process.stdout == (
        "include (list[str]):\n"
        "    An array of glob patterns to include.\n"
        "exclude (list[str], optional):\n"
        "    An array of glob patterns to exclude. (default: [])\n"
        "out_dir (str, optional):\n"
        "    The output path prefix.\n"
        "tag_format (str, optional):\n"
        "    The strftime format of the dest tag. (default: '_v%Y%m%d-%H%M%S')\n"
        "tag_pattern (str, optional):\n"
        "    A regex pattern to match existing dest tags. (default: '_v\\\\d{8}-\\\\d{6}')\n"
        "on_conflict (typing.Literal['error', 'skip', 'overwrite'], optional):\n"
        "    The action of existing dest files. (default: 'error')\n"
        "threads (int, optional):\n"
        "    The number of maximum threads to use. (default: 8)\n"
    )


def test_cli_simple(tmp_path: Path) -> None:
    from h3a.cli import CliResult, main
    from h3a.config import (
        DEFAULT_TAG_FORMAT,
        DEFAULT_TAG_PATTERN,
        DEFAULT_THREADS,
        Config,
    )
    from h3a.plan import format_plan_item

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz/blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text("include:\n  - foo.txt\n")

    # -- Execute cli --
    cli_runner = CliRunner()
    with chdir(tmp_path):
        cli_result = cli_runner.invoke(main, input="y\n", standalone_mode=False)

    # -- Assert cli result --
    assert cli_result.exception is None, cli_result.output
    assert cli_result.exit_code == 0, cli_result.output
    cli_return_value: object = cli_result.return_value
    assert isinstance(cli_return_value, CliResult)

    # -- Assert config --
    assert cli_return_value.config == Config(
        include=["foo.txt"],
        exclude=[],
        out_dir="",
        tag_format=DEFAULT_TAG_FORMAT,
        tag_pattern=DEFAULT_TAG_PATTERN,
        on_conflict="error",
        threads=DEFAULT_THREADS,
    )

    # -- Assert context --
    context = cli_return_value.context
    assert not context.verbose
    assert not context.debug
    assert context.threads == DEFAULT_THREADS

    # -- Assert plan --
    plan = cli_return_value.plan
    assert len(plan) == 1, plan
    assert plan[0].id == 1
    assert isinstance(plan[0].src, Path)
    assert plan[0].src == (tmp_path / "foo.txt")
    assert isinstance(plan[0].dest, Path)
    assert plan[0].dest.parent == tmp_path
    assert re.fullmatch(r"foo_v\d{8}-\d{6}.txt", plan[0].dest.name)
    assert not plan[0].overwrite_flag

    # -- Assert cli output --
    assert cli_result.output.startswith(
        f"Generated plan:\n{format_plan_item(plan[0])}\nContinue? [y/N]: y\nExecuting"
    )

    # -- Assert execution --
    assert set(
        path.relative_to(tmp_path).as_posix() for path in tmp_path.glob("**/*.*")
    ) == {
        "foo.txt",
        "bar.txt",
        "h3a.yaml",
        plan[0].dest.name,
        "baz/blah.txt",
    }
    assert plan[0].src.read_text() == plan[0].dest.read_text()


def test_cli_complex(tmp_path: Path) -> None:
    from h3a.cli import CliResult, main
    from h3a.config import Config
    from h3a.plan import PlanItem, format_plan_item

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive/foo.backup.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / "baz.txt").write_text("bar")
    (tmp_path / "blah").mkdir()
    (tmp_path / "blah/blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n"
        "  - '*.txt'\n"
        "exclude:\n"
        "  - bar.txt\n"
        "out_dir: archive\n"
        "tag_format: .backup\n"
        "tag_pattern: .backup\n"
        "on_conflict: overwrite\n"
        "threads: 2\n"
    )

    # -- Execute cli --
    cli_runner = CliRunner()
    with chdir(tmp_path):
        cli_result = cli_runner.invoke(
            main, ["--verbose", "-t", "1"], input="y\n", standalone_mode=False
        )

    # -- Assert cli result --
    assert cli_result.exception is None, cli_result.output
    assert cli_result.exit_code == 0, cli_result.output
    cli_return_value: object = cli_result.return_value
    assert isinstance(cli_return_value, CliResult)

    # -- Assert config --
    assert cli_return_value.config == Config(
        include=["*.txt"],
        exclude=["bar.txt"],
        out_dir="archive",
        tag_format=".backup",
        tag_pattern=".backup",
        on_conflict="overwrite",
        threads=1,
    )

    # -- Assert context --
    context = cli_return_value.context
    assert context.verbose
    assert not context.debug
    assert context.threads == 1

    # -- Assert plan --
    plan = cli_return_value.plan
    assert list(plan_item.id for plan_item in plan) == list(
        i + 1 for i in range(len(plan))
    )
    assert set(plan_item._replace(id=-1) for plan_item in plan) == {
        PlanItem(
            id=-1,
            src=(tmp_path / "foo.txt"),
            dest=(tmp_path / "archive/foo.backup.txt"),
            overwrite_flag=True,
        ),
        PlanItem(
            id=-1,
            src=(tmp_path / "baz.txt"),
            dest=(tmp_path / "archive/baz.backup.txt"),
            overwrite_flag=False,
        ),
    }

    # -- Assert cli output --
    expected_begin_lines = [
        "Generated plan:",
        f"{format_plan_item(plan[0])}",
        f"{format_plan_item(plan[1])}",
        "Continue? [y/N]: y",
    ]
    n_expected_begin_lines = len(expected_begin_lines)
    actual_lines = cli_result.output.splitlines()
    assert len(actual_lines) == n_expected_begin_lines + 3
    assert actual_lines[:n_expected_begin_lines] == expected_begin_lines
    actions = (
        ("Overwrote", "Created") if plan[0].overwrite_flag else ("Created", "Overwrote")
    )
    assert re.fullmatch(
        TIMESTAMP_PATTERN
        + re.escape(f" INFO (h3a.execute) {actions[0]}: {plan[0].dest} (50.00%)"),
        actual_lines[n_expected_begin_lines],
    )
    assert re.fullmatch(
        TIMESTAMP_PATTERN
        + re.escape(f" INFO (h3a.execute) {actions[1]}: {plan[1].dest} (100.00%)"),
        actual_lines[n_expected_begin_lines + 1],
    )
    assert re.fullmatch(
        TIMESTAMP_PATTERN + re.escape(" INFO (h3a.execute) All done."),
        actual_lines[n_expected_begin_lines + 2],
    )

    # -- Assert execution --
    assert set(
        path.relative_to(tmp_path).as_posix() for path in tmp_path.glob("**/*.*")
    ) == {
        "foo.txt",
        "archive/foo.backup.txt",
        "bar.txt",
        "baz.txt",
        "archive/baz.backup.txt",
        "h3a.yaml",
        "blah/blah.txt",
    }
    for plan_item in plan:
        assert plan_item.src.read_text() == plan_item.dest.read_text()


def test_cli_dry_run(tmp_path: Path) -> None:
    from h3a.cli import CliResult, main
    from h3a.config import (
        DEFAULT_TAG_FORMAT,
        DEFAULT_TAG_PATTERN,
        DEFAULT_THREADS,
        Config,
    )

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz/blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text("include:\n  - foo.txt\n")

    # -- Execute cli --
    cli_runner = CliRunner()
    with chdir(tmp_path):
        cli_result = cli_runner.invoke(
            main, ["--dry-run", "--debug"], input="y\n", standalone_mode=False
        )

    # -- Assert cli result --
    assert cli_result.exception is None, cli_result.output
    assert cli_result.exit_code == 0, cli_result.output
    cli_return_value: object = cli_result.return_value
    assert isinstance(cli_return_value, CliResult)

    # -- Assert config --
    assert cli_return_value.config == Config(
        include=["foo.txt"],
        exclude=[],
        out_dir="",
        tag_format=DEFAULT_TAG_FORMAT,
        tag_pattern=DEFAULT_TAG_PATTERN,
        on_conflict="error",
        threads=DEFAULT_THREADS,
    )

    # -- Assert context --
    context = cli_return_value.context
    assert context.verbose
    assert context.debug
    assert context.threads == DEFAULT_THREADS

    # -- Assert plan --
    plan = cli_return_value.plan
    assert len(plan) == 1, plan
    assert plan[0].id == 1
    assert isinstance(plan[0].src, Path)
    assert plan[0].src == (tmp_path / "foo.txt")
    assert isinstance(plan[0].dest, Path)
    assert plan[0].dest.parent == tmp_path
    assert re.fullmatch(r"foo_v\d{8}-\d{6}.txt", plan[0].dest.name)
    assert not plan[0].overwrite_flag

    # -- Assert execution --
    assert set(
        path.relative_to(tmp_path).as_posix() for path in tmp_path.glob("**/*.*")
    ) == {
        "foo.txt",
        "bar.txt",
        "h3a.yaml",
        "baz/blah.txt",
    }


def test_cli_subprocess(tmp_path_factory: TempPathFactory) -> None:
    # -- Initialize test files --
    file_dir = tmp_path_factory.mktemp("file_dir")
    (file_dir / "foo.txt").write_text("foo")
    (file_dir / "bar.txt").write_text("bar")
    (file_dir / "baz").mkdir()
    (file_dir / "baz/blah.txt").write_text("blah")
    (file_dir / "h3a.yaml").write_text("include:\n  - foo.txt\n")
    file_paths_before = set(
        path.relative_to(file_dir).as_posix() for path in file_dir.glob("**/*.*")
    )

    # -- Execute cli --
    config_path = str((file_dir / "h3a.yaml").absolute())
    with chdir(tmp_path_factory.mktemp("cwd")):
        run(["h3a", "-yc", config_path], check=True)

    # -- Assert execution --
    file_paths_after = set(
        path.relative_to(file_dir).as_posix() for path in file_dir.glob("**/*.*")
    )
    assert len(file_paths_after) == len(file_paths_before) + 1
    new_paths = file_paths_after - file_paths_before
    assert len(new_paths) == 1
    new_path = list(new_paths)[0]
    assert re.fullmatch(r"foo_v\d{8}-\d{6}.txt", new_path)
