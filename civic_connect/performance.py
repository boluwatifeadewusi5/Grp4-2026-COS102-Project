import gc
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional


class PerformanceManager:
    def __init__(self, root, max_workers: int = 1):
        self.root = root
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="civic-db")
        self.last_collect_at = 0.0

    def run(self, work: Callable, on_success: Callable, on_error: Optional[Callable] = None):
        future = self.executor.submit(work)

        def poll():
            if future.done():
                try:
                    result = future.result()
                except Exception as exc:
                    if on_error:
                        on_error(exc)
                    return
                on_success(result)
                return
            self.root.after(35, poll)

        self.root.after(35, poll)
        return future

    def collect(self, force: bool = False):
        now = time.monotonic()
        if force or now - self.last_collect_at >= 4:
            self.last_collect_at = now
            gc.collect()

    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)
