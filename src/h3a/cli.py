import logging
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, NamedTuple

import click

if TYPE_CHECKING:  # pragma: no cover
    from .config import Config
    from .context import Context
    from .plan import Plan


def help_config(context: click.Context, param: click.Parameter, value: object) -> None:
    if not value or context.resilient_parsing:
        return

    from .config import format_config_help

    click.echo(format_config_help(), nl=False)
    context.exit()


class CliResult(NamedTuple):
    config: "Config"
    context: "Context"
    plan: "Plan"


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
    "--help-config",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=help_config,
    help="Show config schema and exit.",
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
    "--dry-run",
    is_flag=True,
    help="Print plan and exit.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable info-level logging.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug-level logging.",
)
@click.version_option()
def main(
    config_file_path: Path,
    config_encoding: str,
    skip_confirm: bool,
    threads: int | None,
    dry_run: bool,
    verbose: bool,
    debug: bool,
) -> CliResult:
    """A simple script for file archiving."""

    if debug:
        verbose = True

    # -- Setup logging --
    logging_level: int = logging.WARNING
    if verbose:
        logging_level = logging.INFO
    if debug:
        logging_level = logging.DEBUG
    logging.basicConfig(
        level=logging_level,
        format="[%(asctime)s] %(levelname)s (%(name)s) %(message)s",
        force=True,
    )
    logger = logging.getLogger(__name__)

    # -- Import APIs --
    from .config import ExtraConfig, load_config
    from .context import Context
    from .execute import execute_plan
    from .plan import format_plan_item, generate_plan

    # -- Load config --
    config_file_path = config_file_path.resolve()
    logger.debug(f"Config file path: {config_file_path!r}")
    extra_config = ExtraConfig()
    config = load_config(
        config_file_path.read_text(encoding=config_encoding),
        extras=extra_config,
    )
    if threads is not None:
        config["threads"] = threads
    logger.debug(f"Config: {config!r}")

    # -- Create context --
    context = Context(
        log_lock=RLock(),
        verbose=verbose,
        debug=debug,
        threads=config["threads"],
        _execute_delay_seconds=extra_config.get("_execute_delay_seconds", None),
    )

    # -- Generate plan --
    plan = generate_plan(
        config=config, root_dir=config_file_path.parent, context=context
    )
    print("Generated plan:")
    for plan_item in plan:
        print(format_plan_item(plan_item))

    if not dry_run:
        # -- Confirm plan --
        if not skip_confirm:
            click.confirm("Continue?", abort=True)

        # -- Execute plan --
        execute_plan(plan, context=context)

    return CliResult(
        config=config,
        context=context,
        plan=plan,
    )
