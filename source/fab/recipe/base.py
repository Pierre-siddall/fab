#!/usr/bin/env python3


from ..logtools import module_loggers


class FabRecipeBase:
    """Fab recipe base class."""

    def __init__(self):
        """Create a pair of loggers for every class."""

        self.build_logger, self.system_logger = module_loggers(__name__)

    def __call__(self, namespace, argv):

        raise NotImplementedError("derived class must override")
