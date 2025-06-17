#!/usr/bin/env python3


"""
Fab command to build and maintain application software.
"""

import sys
import importlib.util
import shutil
from pathlib import Path
from .arguments import ArgumentParser
from ..logtools import make_logger, setup_file_logging
from ..recipe.zero import ZeroConfigRecipe
from ..recipe.base import FabRecipeBase

try:
    import rich.traceback

    HAVE_RICH = True
except ModuleNotFoundError:
    HAVE_RICH = False


def process_arguments(argv):
    """Process command line arguments."""

    fabfile = Path("FabFile")

    parser = ArgumentParser(
        usage="%(prog)s [options]", fabfile=fabfile, description=__doc__
    )
    parser.set_defaults(zero_config=False)

    perf = parser.add_argument_group("performance arguments")

    perf.add_argument(
        "--serial", action="store_true", help="do not use multi-processing"
    )

    perf.add_argument(
        "--two-stage", action="store_true", help="use two-stage fortran mode"
    )

    args, rest = parser.parse_known_args(argv[1:])

    if args.file is None:
        # If the file option has not been supplied, check for a file in
        # the default location.  If something exists and it is a file, use
        # it.  If not, use zero config mode.
        fabfile = fabfile.resolve()

        if fabfile.is_file():
            args.file = fabfile
        else:
            args.zero_config = True

    else:
        # Check that the argument provided by the user has specified
        # exists.  Do not attempt to use zero config mode
        args.file = args.file.resolve()
        if not args.file.exists():
            parser.error(f"specified FabFile does not exist: {args.file}")
        elif not args.file.is_file():
            parser.error(f"specified FabFile is not a regular file: {args.file}")

    return args, rest


def import_from_path(module_name, file_path):
    """Load a module by file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    """Main function."""

    args, rest = process_arguments(argv or sys.argv)

    system = make_logger("fab", "system")

    if HAVE_RICH:
        # Add a more user friendly traceback handler.  Only report the
        # values of local variables when debug output is enabled
        rich.traceback.install(show_locals=args.debug is not None)

    if args.zero_config:
        system.info("using zero config recipe")
        build_class = ZeroConfigRecipe
        project = args.project or "zero-config"

    else:
        system.info("using build file %s", args.file)
        builder = import_from_path("builder", args.file)
        build_class = getattr(builder, "FabRecipe", None)

        if build_class is None:
            system.error("unable to find FabRecipe class in file")
            raise SystemExit(1)

        if not issubclass(build_class, FabRecipeBase):
            system.error("FabRecipe is not a subclass of FabRecipeBase")
            raise SystemExit(1)

        if not hasattr(build_class, "project") or build_class.project is None:
            system.error(f"FabBuild does not define a project name")

    project = args.project or build_class.project
    runner = build_class()

    project_workspace = args.workspace / project

    if args.fresh and project_workspace.exists():
        # This makes an assumption about the workspace path
        system.info("removing old project workspace %s", project_workspace)
        shutil.rmtree(project_workspace)

    setup_file_logging(project_workspace / "fab.log")

    try:
        runner(args, rest)
    except KeyboardInterrupt:
        system.error("interrupted by user")
        raise SystemExit(1)


if __name__ == "__main__":

    main()
