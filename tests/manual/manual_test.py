from pathlib import Path
from shutil import rmtree
from typing import Final, Never
from warnings import warn

from pytest import skip

MANUAL_DIR = Path(__file__).parent
FILE_COUNT: Final = 10


def setup_module() -> None:
    (MANUAL_DIR / "h3a.yaml").write_text(
        "include:\n"
        "  - files/*\n"
        "on_conflict: overwrite\n"
        "threads: 2\n"
        "_execute_delay_seconds: 2\n"
    )
    FILE_DIR = MANUAL_DIR / "files"
    if FILE_DIR.exists():
        rmtree(FILE_DIR)
    FILE_DIR.mkdir()
    for i in range(FILE_COUNT):
        file_name = f"{(i + 1):04d}"
        (FILE_DIR / f"{file_name}.txt").write_text(file_name)


def test_manual() -> Never:
    warn(
        f"!!! Remember to do the manual test in {MANUAL_DIR.relative_to(Path.cwd())} !!!"
    )
    skip()
