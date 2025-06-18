#!/usr/bin/env python3
##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################
"""
Progress tracking.
"""


import contextlib
import time
import inspect
from .logtools import make_logger


try:
    import rich.console

    HAVE_RICH = True
except ModuleNotFoundError:
    HAVE_RICH = False


# pylint: disable=too-few-public-methods


class Progress:
    """Decorator to track and log progress of functions."""

    # Switch off all spinners if Progress.quiet is True
    quiet = False

    def __init__(self, *args, **kwargs):

        self._func = None

        self.caption = kwargs.pop("caption", None)
        self.prologue = kwargs.pop("prologue", None)
        self.epilogue = kwargs.pop("epilogue", None)
        self.duration = kwargs.pop("duration", False)

        if args and callable(args[0]):
            # Decorator without arguments
            self._func = args[0]

    def __call__(self, *args, **kwargs):

        if self._func is None and callable(args[0]):
            # Setup the decorated function
            self._func = args[0]
            return self.__inner

        if self._func is None:
            raise TypeError("unable to find appropriate function")

        # Run the decorated functions
        return self.__inner(*args, **kwargs)

    def __inner(self, *args, **kwargs):

        # Get the module that contains the calling function and use
        # that to name the logger
        name = inspect.getmodule(self._func).__name__
        logger = make_logger(name, "build")

        if self.prologue is not None:
            logger.info(self.prologue.format(*args, **kwargs))

        if HAVE_RICH and self.caption is not None and not Progress.quiet:
            # FIXME: this should probably be a single console instance
            console = rich.console.Console()
            display = console.status(self.caption.format(*args, **kwargs))
        else:
            display = contextlib.nullcontext(None)

        with display:
            t0 = time.time()
            rc = self._func(*args, **kwargs)
            tdelta = time.time() - t0
            time.sleep(2)

        # FIXME: Add metrics support

        if self.epilogue is not None:
            message = self.epilogue
            if self.duration:
                message += " (duration: {duration:.3f}s)"
            logger.info(message.format(*args, **kwargs, duration=tdelta))

        return rc


class ProgressSpinner(Progress):
    """Decorator to report progress with log messages and a spinner."""

    def __init__(self, caption, epilogue, duration=False):
        super().__init__(caption=caption, epilogue=epilogue, duration=duration)


class ProgressReport(Progress):
    """Decorator to report progress with log messages."""

    def __init__(self, epilogue, prologue=None, duration=False):
        super().__init__(epilogue=epilogue, prologue=prologue, duration=duration)
