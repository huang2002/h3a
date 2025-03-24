import re
from fnmatch import fnmatch
from glob import glob
from logging import getLogger
from pathlib import Path
from time import strftime
from typing import NamedTuple

from .config import Config
from .context import Context

logger = getLogger(__name__)


def collect_target_files(root_dir: Path, config: Config) -> set[Path]:
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


type Plan = list[PlanItem]


def generate_plan(*, config: Config, root_dir: Path, context: Context) -> Plan:
    tag = strftime(config["tag_format"])
    if not re.fullmatch(config["tag_pattern"], tag):
        raise RuntimeError(
            f"Generated tag {tag!r} is incompatible with "
            f"tag pattern: {config['tag_pattern']!r}"
        )

    tag_length = len(tag)
    plan: Plan = []
    target_files = collect_target_files(root_dir, config)
    conflict_paths = set[Path]()
    skipped_paths = set[Path]()

    for src_path in target_files:
        if re.fullmatch(config["tag_pattern"], src_path.stem[-tag_length:]):
            skipped_paths.add(src_path)
            with context.log_lock:
                logger.warning(f"Skipping file with matched tag: {src_path}")
            continue

        overwrite_flag = False

        dest_path = src_path.with_stem(src_path.stem + tag)
        if dest_path.exists():
            if dest_path in target_files:
                conflict_paths.add(dest_path)

            match config["on_conflict"]:
                case "error":
                    raise RuntimeError(f"Destination file exists: {dest_path}")
                case "skip":
                    with context.log_lock:
                        logger.warning(
                            f"Skipping existing destination file: {dest_path}"
                        )
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

    conflict_paths -= skipped_paths
    if len(conflict_paths):
        raise RuntimeError(
            f"Detected destination file conflict(s): {', '.join(map(str, conflict_paths))}"
        )

    return plan
