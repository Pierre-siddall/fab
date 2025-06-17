#!/usr/bin/env python3


"""
Module containing logging tools for the user-facing fab commannd.
"""


import logging
import pathlib

try:
    from rich.logging import RichHandler
except ModuleNotFoundError:
    RichHandler = None


def module_loggers(module):
    """Create a build and system loggers for a module."""

    return (make_logger(module, "build"), make_logger(module, "system"))


def make_logger(module, feature):
    """Create a hierarchical logger.

    Given the name of a module and a target feature, typically either
    build or system, create a logger instance by injecting the feature
    name as the second element in the naming hierarchy.

    This is intended to be used to allow each module to define its own
    logger but to allow different output levels to be set
    independently for different categories of logger.

    Module names with underscores are cleaned up to make the names
    more sensible.
    """

    parts = module.split(".")

    # Clean up the name a bit
    if parts[-1] == "__init__":
        del parts[-1]
    parts = [i.replace("__", "") for i in parts]

    # Insert the feature into the naming hierarchy
    parts.insert(1, feature)

    # Create the logger with an appropriate name
    return logging.getLogger(".".join(parts))


def setup_logging(build_level, system_level, quiet=False):
    """Setup the fab logging framework.

    Set output levels for build log messages and system log messages.

    Build messages are purely intended to be used to output
    information about the compile tasks.  System messages should help
    to debug the fab library itself.

    If the Rich library is available, its logging handler is used in
    place of the standard python handler, and more information about
    the location of log messages is added to the output when system
    level logging is enabled.
    """

    parent = logging.getLogger("fab")

    # This is the root logger for user-centric build output messages
    build = logging.getLogger("fab.build")
    if build_level is None:
        build.setLevel(logging.WARNING)
    elif build_level == 1:
        build.setLevel(logging.INFO)
    else:
        build.setLevel(logging.DEBUG)

    # This is the output for internal fab system messages intended to
    # to provide debugging information
    internal = logging.getLogger("fab.system")
    if system_level is None or system_level == 0:
        internal.setLevel(logging.WARNING)
    elif system_level == 1:
        internal.setLevel(logging.INFO)
    else:
        internal.setLevel(logging.DEBUG)

    # settings = {"level": logging.DEBUG, "datefmt": "[%F %X]"}

    if RichHandler is None:
        # Basic python logging
        if system_level is None:
            formatter = logging.Formatter("%(asctime)s %(message)s")
        else:
            formatter = logging.Formatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)

    else:
        # Improved formatting using the rich framework
        if system_level is None or system_level == 0:
            handler_args = {"show_level": False, "show_path": False}
        else:
            # if system_level > 2:
            #    settings["format"] = "%(name)-28s %(message)s"
            handler_args = {"show_level": True, "show_path": True}

        stream = RichHandler(**handler_args)

    parent.addHandler(stream)
    stream.setLevel(logging.ERROR if quiet else logging.DEBUG)


def setup_file_logging(logfile, parent="fab", create=True):
    """Send log messages to a file."""

    logfile = pathlib.Path(logfile)

    if create and not logfile.parent.is_dir():
        logfile.parent.mkdir(parents=True)

    logfm = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logfh = logging.FileHandler(logfile)
    logfh.setLevel(logging.DEBUG)
    logfh.setFormatter(logfm)
    logging.getLogger(parent).addHandler(logfh)


if __name__ == "__main__":

    setup_logging(1, 0)
    logging.info("Test")
