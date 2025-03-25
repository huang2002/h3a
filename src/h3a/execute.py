from concurrent.futures import ThreadPoolExecutor
from functools import partial
from logging import getLogger
from shutil import copy2
from threading import RLock
from time import sleep

from click import progressbar

from .context import Context
from .plan import Plan, PlanItem

logger = getLogger(__name__)


class ExecuteProgress:
    lock: RLock
    finished: int
    total: int

    def __init__(self, total: int) -> None:
        self.lock = RLock()
        self.finished = 0
        self.total = total

    def step(self) -> float:
        with self.lock:
            assert self.finished < self.total
            self.finished += 1
            return self.finished / self.total


def execute_plan_item(
    plan_item: PlanItem, *, context: Context, progress: ExecuteProgress
) -> None:
    with context.log_lock:
        logger.debug(f"Executing plan item: {plan_item!r}")

    plan_item.dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(plan_item.src, plan_item.dest)

    if context._execute_delay_seconds is not None:
        assert isinstance(context._execute_delay_seconds, float)
        sleep(context._execute_delay_seconds)

    precentage = progress.step()

    with context.log_lock:
        if plan_item.overwrite_flag:
            logger.info(f"Overwrote: {plan_item.dest} ({precentage:.2%})")
        else:
            logger.info(f"Created: {plan_item.dest} ({precentage:.2%})")


def execute_plan(plan: Plan, *, context: Context) -> None:
    progress = ExecuteProgress(len(plan))

    with ThreadPoolExecutor(max_workers=context.threads) as executor:
        execute_results_iterable = executor.map(
            partial(execute_plan_item, context=context, progress=progress),
            plan,
        )

        # Retrieve results to throw exceptions from threads.
        # (The following code must be put in the with statement because
        # the progresses must be collected before exiting the with statement.)
        if context.verbose:
            for _ in execute_results_iterable:
                pass
        else:
            with progressbar(
                execute_results_iterable, label="Executing", length=len(plan)
            ) as execute_results:
                for _ in execute_results:
                    pass

    with context.log_lock:
        logger.info("All done.")
