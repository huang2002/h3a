import logging
from pathlib import Path
from threading import RLock

import click

from .config import load_config
from .context import Context
from .execute import execute_plan
from .plan import Plan, generate_plan

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "config_file_path",
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, allow_dash=True, path_type=Path),
    default="h3a.yaml",
    help="Path to config file.",
    show_default=True,
)
@click.option(
    "config_encoding",
    "-e",
    "--encoding",
    default="utf-8",
    help="Encoding of the config file.",
    show_default=True,
)
@click.option(
    "-y",
    "--skip-confirm",
    is_flag=True,
    help="Skip confirmation prompt.",
)
@click.option(
    "-t",
    "--threads",
    type=click.IntRange(min=1),
    help="Number of threads to use.",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Print plan and exit.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable debug logging.",
)
@click.version_option()
def main(
    config_file_path: Path,
    config_encoding: str,
    skip_confirm: bool,
    threads: int | None,
    dry_run: bool,
    verbose: bool,
) -> Plan:
    """A simple script for file archiving."""

    # -- Setup logging --
    logging.basicConfig(format="%(asctime)s [%(levelname)5s] (%(name)s) %(message)s")
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    # -- Load config --
    config_file_path = config_file_path.resolve()
    logger.debug(f"Config file path: {config_file_path!r}")
    config = load_config(config_file_path, encoding=config_encoding)
    if threads is not None:
        config["threads"] = threads
    logger.debug(f"Config: {config!r}")

    # -- Create context --
    context = Context(
        log_lock=RLock(),
        verbose=verbose,
        threads=config["threads"],
    )

    # -- Generate plan --
    plan = generate_plan(
        config=config, root_dir=config_file_path.parent, context=context
    )
    print("Generated plan:")
    for plan_item in plan:
        print("- " + repr(plan_item))

    if not dry_run:
        # -- Confirm plan --
        if not skip_confirm:
            click.confirm("Continue?", abort=True)

        # -- Execute plan --
        execute_plan(plan, context=context)

    return plan
