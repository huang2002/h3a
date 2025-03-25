import re
from pathlib import Path
from typing import TYPE_CHECKING

from pytest import raises

if TYPE_CHECKING:
    from h3a.context import Context  # pragma: no cover


def test_plan_simple(tmp_path: Path, test_context: "Context") -> None:
    from h3a.config import load_config
    from h3a.plan import PlanItem, generate_plan

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "foo_v20021011-123456.txt").write_text("foo")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz/blah.txt").write_text("blah")
    (tmp_path / "h3a.yaml").write_text("include:\n  - '*.txt'\n")

    # -- Generate plan --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    plan = generate_plan(config=config, root_dir=tmp_path, context=test_context)
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


def test_plan_tag_unmatch(tmp_path: Path, test_context: "Context") -> None:
    from h3a.config import load_config
    from h3a.plan import generate_plan

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "foo_backup.txt").write_text("foo")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n  - foo.txt\ntag_format: .backup\ntag_pattern: _backup\n"
    )

    # -- Generate plan --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    with raises(
        RuntimeError,
        match="Generated tag '.backup' is incompatible with tag pattern: '_backup'",
    ):
        _plan = generate_plan(config=config, root_dir=tmp_path, context=test_context)


def test_plan_conflict_error(tmp_path: Path, test_context: "Context") -> None:
    from h3a.config import load_config
    from h3a.plan import generate_plan

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "foo_backup.txt").write_text("foo")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n  - foo.txt\ntag_format: _backup\ntag_pattern: _backup\n"
    )

    # -- Generate plan --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    with raises(
        RuntimeError, match=f"Destination file exists: {tmp_path / 'foo_backup.txt'}"
    ):
        _plan = generate_plan(config=config, root_dir=tmp_path, context=test_context)


def test_plan_conflict_skip(tmp_path: Path, test_context: "Context") -> None:
    from h3a.config import load_config
    from h3a.plan import PlanItem, generate_plan

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "foo_backup.txt").write_text("foo")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n"
        "  - foo.txt\n"
        "tag_format: _backup\n"
        "tag_pattern: _backup\n"
        "on_conflict: skip\n"
    )

    # -- Generate plan --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    plan = generate_plan(config=config, root_dir=tmp_path, context=test_context)
    assert isinstance(plan, list)
    assert all(isinstance(plan_item, PlanItem) for plan_item in plan)
    assert len(plan) == 0


def test_plan_overwriting_src(tmp_path: Path, test_context: "Context") -> None:
    from h3a.config import load_config
    from h3a.plan import generate_plan

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "foo_backup.txt").write_text("foo")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n  - foo.txt\ntag_format: .backup\ntag_pattern: _backup\n"
    )

    # -- Generate plan --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    with raises(
        RuntimeError,
        match="Generated tag '.backup' is incompatible with tag pattern: '_backup'",
    ):
        _plan = generate_plan(config=config, root_dir=tmp_path, context=test_context)


def test_plan_complex(tmp_path: Path, test_context: "Context") -> None:
    from time import strftime

    from h3a.config import load_config
    from h3a.plan import PlanItem, generate_plan

    # -- Initialize test files --
    (tmp_path / "foo.txt").write_text("foo")
    (tmp_path / "bar.txt").write_text("bar")
    (tmp_path / f"bar__{strftime('%Y%m%d')}.txt").write_text("bar")
    (tmp_path / "baz").mkdir()
    (tmp_path / "baz/a.txt").write_text("a")
    (tmp_path / "baz/b.txt").write_text("b")
    (tmp_path / "baz/c").mkdir()
    (tmp_path / "baz/c/0.txt").write_text("0")
    (tmp_path / "baz/c/1.txt").write_text("1")
    (tmp_path / "baz/c/2.txt").write_text("2")
    (tmp_path / "h3a.yaml").write_text(
        "include:\n"
        "  - '*.txt'\n"
        "  - baz/a.txt\n"
        "  - baz/c/**\n"
        "exclude:\n"
        "  - foo.txt\n"
        "  - baz/c/1.txt\n"
        "on_conflict: overwrite\n"
        "tag_format: __%Y%m%d\n"
        "tag_pattern: '__\\d{8}'\n"
    )

    # -- Generate plan --
    config = load_config((tmp_path / "h3a.yaml").read_text())
    plan = generate_plan(config=config, root_dir=tmp_path, context=test_context)
    assert isinstance(plan, list)
    assert all(isinstance(plan_item, PlanItem) for plan_item in plan)

    # -- Assert plan content --
    assert len(plan) == 4, plan
    assert {plan_item.src for plan_item in plan} == {
        tmp_path / "bar.txt",
        tmp_path / "baz/a.txt",
        tmp_path / "baz/c/0.txt",
        tmp_path / "baz/c/2.txt",
    }
    for i, plan_item in enumerate(plan):
        assert plan_item.id == i + 1
        assert isinstance(plan_item.src, Path)
        assert tmp_path in plan_item.src.parents
        assert isinstance(plan_item.dest, Path)
        assert tmp_path in plan_item.dest.parents
        expected_dest_name = (
            plan_item.src.stem + strftime("__%Y%m%d") + plan_item.dest.suffix
        )
        assert plan_item.dest.name == expected_dest_name
        assert plan_item.overwrite_flag == plan_item.dest.exists()
