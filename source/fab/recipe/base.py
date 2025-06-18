#!/usr/bin/env python3
##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################

from ..logtools import module_loggers


class FabRecipeBase:
    """Fab recipe base class."""

    def __init__(self):
        """Create a pair of loggers for every class."""

        self.build_logger, self.system_logger = module_loggers(__name__)

    def __call__(self, namespace, argv):

        raise NotImplementedError("derived class must override")
