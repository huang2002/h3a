import re
from fnmatch import fnmatch
from glob import glob
from logging import getLogger
from pathlib import Path
from time import localtime, strftime
from typing import NamedTuple, assert_never

from .config import Config
from .context import Context

logger = getLogger(__name__)


def collect_source_files(root_dir: Path, config: Config) -> set[Path]:
    return set(
        (root_dir / path).absolute()
        for include_pattern in config["include"]
        for path in glob(include_pattern, root_dir=root_dir, recursive=True)
        if (
            (root_dir / path).is_file()
            and not any(
                fnmatch(path, exclude_pattern) for exclude_pattern in config["exclude"]
            )
        )
    )


class PlanItem(NamedTuple):
    id: int
    src: Path
    dest: Path
    overwrite_flag: bool


def format_plan_item(plan_item: PlanItem) -> str:
    arrow: str = "~>" if plan_item.overwrite_flag else "->"
    return f"({plan_item.id}) {plan_item.src} {arrow} {plan_item.dest}"


def assert_tag_pattern(tag: str, tag_pattern: str) -> None:
    if not re.fullmatch(tag_pattern, tag):
        raise RuntimeError(
            f"Generated tag {tag!r} is incompatible with tag pattern: {tag_pattern!r}"
        )


type Plan = list[PlanItem]


def generate_plan(*, config: Config, root_dir: Path, context: Context) -> Plan:
    init_tag = strftime(config["tag_format"])
    assert_tag_pattern(init_tag, config["tag_pattern"])

    tag_length = len(init_tag)
    out_dir = (root_dir / config["out_dir"]).resolve()
    plan: Plan = []
    src_paths = collect_source_files(root_dir, config)
    overwriting_src_paths = set[Path]()
    skipped_paths = set[Path]()

    for src_path in src_paths:
        if re.fullmatch(config["tag_pattern"], src_path.stem[-tag_length:]):
            skipped_paths.add(src_path)
            with context.log_lock:
                logger.info(f"Skipping file with matched tag: {src_path}")
            continue

        overwrite_flag = False

        tag: str
        match config["tag_time_source"]:
            case "now":
                tag = init_tag
            case "mtime":
                time = localtime(src_path.stat().st_mtime)
                tag = strftime(config["tag_format"], time)
            case "ctime":
                time = localtime(src_path.stat().st_ctime)
                tag = strftime(config["tag_format"], time)
            case _:  # pragma: no cover
                assert_never(config["tag_time_source"])
        assert_tag_pattern(tag, config["tag_pattern"])

        assert src_path.is_relative_to(root_dir)
        dest_stem = src_path.stem + tag
        relative_dest_path = src_path.with_stem(dest_stem).relative_to(root_dir)
        dest_path = out_dir / relative_dest_path

        if dest_path.exists():
            if dest_path in src_paths:
                overwriting_src_paths.add(dest_path)

            match config["on_conflict"]:
                case "error":
                    raise RuntimeError(f"Destination file exists: {dest_path}")
                case "skip":
                    with context.log_lock:
                        logger.info(f"Skipping existing destination file: {dest_path}")
                    continue
                case "overwrite":
                    overwrite_flag = True
                    with context.log_lock:
                        logger.debug(
                            f"Overwriting existing destination file: {dest_path}"
                        )

        plan.append(
            PlanItem(
                id=(len(plan) + 1),
                src=src_path,
                dest=dest_path,
                overwrite_flag=overwrite_flag,
            )
        )

    overwriting_src_paths -= skipped_paths
    if len(overwriting_src_paths):
        # This should never happen because source files conflicting with
        # destination files should have tags matched and thus be skipped.
        raise RuntimeError(  # pragma: no cover
            f"Overwriting source file(s): {', '.join(map(str, overwriting_src_paths))}"
        )

    return plan
