##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################
"""
Flexible build system for scientific software.

"""
import sys

__version__ = '1.1.dev0'


class FabException(Exception):
    pass


class FabRuntimeError(RuntimeError):
    pass


class CommandAvailableError(FabRuntimeError):

    def __init__(self, name):
        super().__init__(f"command {repr(name)} is not available")


class CommandRuntimeError(FabRuntimeError):
    def __init__(self, name, rc, command, output, error):
        self.name = name
        self.rc = int(rc)
        self.command = command
        self.output = output
        self.error = error
        super().__init__(f"command {repr(command)} returned {rc}")
