#!/usr/bin/env python3
##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################
"""
Parallel processing tools which report progress.
"""

import multiprocessing
import contextlib
from concurrent.futures import ProcessPoolExecutor


try:
    import rich.progress

    HAVE_RICH = True
except ModuleNotFoundError:
    HAVE_RICH = False


class WorkerPool:
    """Class which runs tasks in parallel and displays progress."""

    # Quiet output is a class setting
    quiet = False

    def __init__(self, nprocs):

        self.nprocs = int(nprocs)

    @staticmethod
    def inner(function, item, counter):
        """Wrapper method which updates a progress counter."""
        result = function(item)
        counter.value += 1
        return result

    def __call__(self, func, items, description, transient=True, callback=None):

        if not items:
            # Return an empty tuple if the item list is empty
            return ()

        if HAVE_RICH and not self.quiet:
            # Disple a progress bar if one has been requested
            display = rich.progress.Progress(
                "[progress.description]{task.description}",
                rich.progress.BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                rich.progress.TimeRemainingColumn(),
                rich.progress.TimeElapsedColumn(),
                transient=transient,
            )
        else:
            # Dummy context to prevent output
            display = contextlib.nullcontext(None)

        with display as progress:
            if progress is not None:
                taskbar = progress.add_task(f"[green]{description}:")
            else:
                taskbar = None

            return self._run_tasks(func, items, progress, taskbar, callback)

    def _run_tasks(self, func, items, progress, taskbar, callback):

        total = len(items)
        tasks = []
        with multiprocessing.Manager() as manager:
            # Create a shared value to track completed work
            complete = manager.Value(int, 0)

            def done(mytask):
                if progress is not None:
                    progress.update(taskbar, completed=complete.value, total=total)
                if callback is not None:
                    callback(mytask.result())

            with ProcessPoolExecutor(max_workers=self.nprocs) as executor:
                for i in items:
                    tasks.append(executor.submit(self.inner, func, i, complete))
                    tasks[-1].add_done_callback(done)

        # Merge the results together
        results = []
        for future in tasks:
            results.append(future.result())

        # Make the results immutable
        return tuple(results)
