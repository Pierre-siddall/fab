#!/usr/bin/env python3

"""
Zero configuration mode.
"""

from argparse import ArgumentParser
from pathlib import Path
from ..logtools import module_loggers
from ..tools import Category, ToolBox, ToolRepository
from ..build_config import BuildConfig
from ..steps.grab.folder import grab_folder
from ..steps.find_source_files import find_source_files
from ..steps.preprocess import preprocess_fortran
from fab.steps.c_pragma_injector import c_pragma_injector
from ..steps.analyse import analyse
from fab.steps.compile_fortran import compile_fortran
from fab.steps.compile_c import compile_c
from fab.steps.link import link_exe
from .base import FabRecipeBase


class ZeroConfigRecipe(FabRecipeBase):

    project = "zero-config"

    def __call__(self, args, rest):
        """Run in zero configuration mode."""

        parser = ArgumentParser(
            usage="%(prog)s [options] source",
            prog=args._progname,
            description=__doc__,
        )
        parser.add_argument("source", type=Path, help="source directory")
        parser.parse_args(rest, args)

        if not args.source.is_dir():
            parser.error("a source directory is required")

        project_label = args.project or "zero-config"
        kwargs = {"fab_workspace": args.workspace}

        self.system_logger.info("configuring the build tools")
        tr = ToolRepository()
        fc = tr.get_default(Category.FORTRAN_COMPILER, mpi=False, openmp=False)
        linker = tr.get_tool(Category.LINKER, f"linker-{fc.name}")

        tool_box = ToolBox()
        tool_box.add_tool(fc)
        tool_box.add_tool(linker)

        with BuildConfig(
            project_label=project_label,
            mpi=False,
            openmp=False,
            tool_box=tool_box,
            **kwargs,
        ) as config:

            grab_folder(config, args.source)
            find_source_files(config)
            preprocess_fortran(config)
            c_pragma_injector(config)
            analyse(config, find_programs=True)
            compile_fortran(config)
            compile_c(config)
            link_exe(config, flags=[])
