from pathlib import Path


def test_config_help() -> None:
    from h3a.config import format_config_help

    assert format_config_help() == (
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


def test_config_simple(tmp_path: Path) -> None:
    from h3a.config import (
        DEFAULT_TAG_FORMAT,
        DEFAULT_TAG_PATTERN,
        DEFAULT_THREADS,
        Config,
        load_config,
    )

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz/blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text("include:\n  - foo.txt\n")

    # -- Load config --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    assert isinstance(config, dict)

    # -- Assert config content --
    assert config == Config(
        include=["foo.txt"],
        exclude=[],
        out_dir="",
        tag_format=DEFAULT_TAG_FORMAT,
        tag_pattern=DEFAULT_TAG_PATTERN,
        on_conflict="error",
        threads=DEFAULT_THREADS,
    )


def test_config_complex(tmp_path: Path) -> None:
    from h3a.config import Config, load_config

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz/blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n"
        "  - foo.txt\n"
        '  - "bar/*.py"\n'
        '  - "**/baz.txt"\n'
        "exclude:\n"
        "  - bar/baz.txt\n"
        "out_dir: archive\n"
        "tag_format: _%Y%m%d\n"
        "tag_pattern: '_\\d{8}'\n"
        "on_conflict: skip\n"
        "threads: 256\n"
    )

    # -- Load config --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    assert isinstance(config, dict)

    # -- Assert config content --
    assert config == Config(
        include=["foo.txt", "bar/*.py", "**/baz.txt"],
        exclude=["bar/baz.txt"],
        out_dir="archive",
        tag_format="_%Y%m%d",
        tag_pattern=r"_\d{8}",
        on_conflict="skip",
        threads=256,
    )
