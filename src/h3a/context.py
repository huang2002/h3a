from dataclasses import dataclass
from threading import RLock


@dataclass
class Context:
    log_lock: RLock
    verbose: bool
    threads: int
