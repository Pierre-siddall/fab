##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################

'''A simple init file to make it shorter to import tools.
'''

from fab.tools.ar import Ar
from fab.tools.category import Category
from fab.tools.compiler import (CCompiler, Compiler, Craycc, Crayftn,
                                FortranCompiler, Gcc, Gfortran, Icc,
                                Icx, Ifort, Ifx, Nvc, Nvfortran)
from fab.tools.compiler_wrapper import (CompilerWrapper, CrayCcWrapper,
                                        CrayFtnWrapper, Mpicc, Mpif90)
from fab.tools.flags import Flags, ProfileFlags
from fab.tools.linker import Linker
from fab.tools.psyclone import Psyclone
from fab.tools.rsync import Rsync
from fab.tools.preprocessor import Cpp, CppFortran, Fpp, Preprocessor
from fab.tools.shell import Shell
from fab.tools.tool import Tool, CompilerSuiteTool
# Order here is important to avoid a circular import
from fab.tools.tool_repository import ToolRepository
from fab.tools.tool_box import ToolBox
from fab.tools.versioning import Fcm, Git, Subversion, Versioning

__all__ = ["Ar",
           "Category",
           "CCompiler",
           "Compiler",
           "CompilerSuiteTool",
           "CompilerWrapper",
           "Cpp",
           "CppFortran",
           "Craycc",
           "CrayCcWrapper",
           "Crayftn",
           "CrayFtnWrapper",
           "Fcm",
           "Flags",
           "FortranCompiler",
           "Fpp",
           "Gcc",
           "Gfortran",
           "Git",
           "Icc",
           "Icx",
           "Ifort",
           "Ifx",
           "Linker",
           "Mpif90",
           "Mpicc",
           "Nvc",
           "Nvfortran",
           "Preprocessor",
           "ProfileFlags",
           "Psyclone",
           "Rsync",
           "Shell",
           "Subversion",
           "Tool",
           "ToolBox",
           "ToolRepository",
           "Versioning",
           ]
