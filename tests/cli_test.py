import re
from contextlib import chdir
from pathlib import Path
from subprocess import run

from click.testing import CliRunner
from pytest import TempPathFactory


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
        "  -d, --dry-run                Print plan and exit.\n"
        "  --verbose                    Enable debug logging.\n"
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
        "tag_format (str, optional):\n"
        "    The strftime format of the dest tag. (default: '_v%Y%m%d-%H%M%S')\n"
        "tag_pattern (str, optional):\n"
        "    A regex pattern to match existing dest tags. (default: '_v\\\\d{8}-\\\\d{6}')\n"
        "on_conflict (typing.Literal['error', 'skip', 'overwrite'], optional):\n"
        "    The action of existing dest files. (default: 'error')\n"
        "threads (int, optional):\n"
        "    The number of maximum threads to use. (default: 16)\n"
    )


def test_cli_simple(tmp_path: Path) -> None:
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
    (tmp_path / "baz" / "blah.txt").write_text("blah")
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
        tag_format=DEFAULT_TAG_FORMAT,
        tag_pattern=DEFAULT_TAG_PATTERN,
        on_conflict="error",
        threads=DEFAULT_THREADS,
    )

    # -- Assert context --
    context = cli_return_value.context
    assert context.verbose == False
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


def test_cli_subprocess(tmp_path_factory: TempPathFactory) -> None:
    # -- Initialize test files --
    file_dir = tmp_path_factory.mktemp("file_dir")
    (file_dir / "foo.txt").write_text("foo")
    (file_dir / "bar.txt").write_text("bar")
    (file_dir / "baz").mkdir()
    (file_dir / "baz" / "blah.txt").write_text("blah")
    (file_dir / "h3a.yaml").write_text("include:\n  - foo.txt\n")
    file_paths_before = set(file_path.name for file_path in file_dir.iterdir())

    # -- Execute cli --
    config_path = str((file_dir / "h3a.yaml").absolute())
    with chdir(tmp_path_factory.mktemp("cwd")):
        run(["h3a", "-yc", config_path], check=True)

    # -- Assert execution --
    file_paths_after = set(file_path.name for file_path in file_dir.iterdir())
    assert len(file_paths_after) == len(file_paths_before) + 1
    new_paths = file_paths_after - file_paths_before
    assert len(new_paths) == 1
    new_path = list(new_paths)[0]
    assert re.fullmatch(r"foo_v\d{8}-\d{6}.txt", new_path)
    assert set(file_path.name for file_path in (file_dir / "baz").iterdir()) == {
        "blah.txt"
    }
