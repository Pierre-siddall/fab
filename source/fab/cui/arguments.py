#!/usr/bin/env python3


"""
Common argument handling features used by fab.
"""


import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from .. import __version__ as fab_version
from ..logtools import setup_logging, make_logger


def FullPath(opt):
    """Expand usernames and resolve links."""
    return Path(opt).expanduser().resolve()


class _FabVersionAction(argparse._VersionAction):
    """Class which reports a fab version ID."""

    def __call__(self, parser, namespace, values, option_string=None):
        version = str(getattr(self, "version", ""))

        if not version or not version.startswith("%(prog)s"):
            # Try to include the program name
            version = "%(prog)s "

        if getattr(self, "version", None) is None:
            # Use the fab version unless the caller has specified
            # something
            version += f"{fab_version}"
        else:
            version += str(self.version)

        self.version = version

        return super().__call__(parser, namespace, values, option_string)


class ArgumentParser(argparse.ArgumentParser):
    """Fab argument parser class.

    This extends the features of the default argparse ArgumentParser
    class to add arguments that might be used by a number of fab
    commands line tools.
    """

    def __init__(self, *args, **kwargs):

        version = kwargs.pop("version", None)
        self.fabfile = kwargs.pop("fabfile", None)

        super().__init__(*args, **kwargs)

        if self.prog == "__main__.py" and self.prog not in kwargs:
            # Try to pick up a better program name from the environment
            # or just use a default string
            self.prog = os.environ.get("__PROGNAME", "fab")

        self.version = version
        self.register("action", "version", _FabVersionAction)
        self._have_logging = False

    def parse_args(self, *args, **kwargs):

        self._setup_args()
        args = super().parse_args(*args, **kwargs)
        args._progname = self.prog
        self._setup_logging(args)
        return args

    def parse_known_args(self, *args, **kwargs):

        self._setup_args()
        args, rest = super().parse_known_args(*args, **kwargs)
        args._progname = self.prog
        self._setup_logging(args)
        if args.help_cmd:
            # Add the help to the list of items passed to the recipe
            rest.insert(0, "--help")
        return args, rest

    def _setup_args(self):
        self.add_argument(
            "--help-cmd", action="store_true", help="display the build recipe help"
        )

        self._add_version_arg()
        self._add_verbose_arg()
        self._add_location_args()

    def _setup_logging(self, args):

        if self._have_logging:
            return

        setup_logging(
            getattr(args, "verbose", None),
            getattr(args, "debug", None),
            getattr(args, "quiet", False),
        )

        logger = make_logger(__name__, "system")
        logger.debug("command line arguments are %s", args)

        self._have_logging = True

    def _add_version_arg(self):
        """Add --version argument if not present."""
        if "--version" not in self._option_string_actions:
            self._optionals.add_argument(
                "--version",
                "-V",
                action="version",
                version=self.version,
                help="show the software version",
            )

    def _add_verbose_arg(self):
        """Add --verbose argument if not present."""

        # FIXME: allow the output group to be extended?
        # Create a logging group
        logargs = self.add_argument_group("output arguments")

        if (
            "--debug" not in self._option_string_actions
            and "-d" not in self._option_string_actions
        ):
            # Add a logging option
            logargs.add_argument(
                "--debug",
                "-d",
                action="count",
                help="increase the amount of fab debug output",
            )

        if (
            "--verbose" not in self._option_string_actions
            and "-v" not in self._option_string_actions
        ):
            # Add a logging option
            logargs.add_argument(
                "--verbose",
                "-v",
                action="count",
                help="increase the amount of build output",
            )

        # Add a quiet option to suppress all/most output
        if (
            "--quiet" not in self._option_string_actions
            and "-q" not in self._option_string_actions
        ):
            # Add a logging option
            logargs.add_argument(
                "--quiet",
                "-q",
                action="store_true",
                help="do not produce much output",
            )

    def _add_location_args(self):
        """Add project, workspace, and fabfile args."""
        fab = self.add_argument_group("location arguments")

        if self.fabfile is not None:
            fab.add_argument(
                "--file",
                type=FullPath,
                metavar="FILE",
                help=f"fab build script (default: {self.fabfile})",
            )

        fab.add_argument(
            "--fresh", action="store_true", help="create a fresh build tree"
        )

        fab.add_argument(
            "--project", type=str, metavar="NAME", help="name to assign to the project"
        )

        fab.add_argument(
            "--workspace",
            type=FullPath,
            metavar="DIR",
            default=os.getenv("FAB_WORKSPACE", "~/fab-workspace"),
            help="location of working space (default: %(default)s)",
        )
