from dataclasses import dataclass
from threading import RLock


@dataclass
class Context:
    log_lock: RLock
    verbose: bool
    debug: bool
    threads: int
    _execute_delay_seconds: float | None = None
