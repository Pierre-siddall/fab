# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################
"""
Common functionality for both Fortran and (sanitised) X90 processing.

"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple, Type, Union

from fparser.common.readfortran import FortranFileReader  # type: ignore
from fparser.two.parser import ParserFactory  # type: ignore
from fparser.two.utils import FortranSyntaxError  # type: ignore

from fab import FabException
from fab.build_config import BuildConfig
from fab.dep_tree import AnalysedDependent
from fab.parse import EmptySourceFile
from fab.util import log_or_dot, file_checksum


logger = logging.getLogger(__name__)


def _typed_child(parent, child_type: Type, must_exist=False):
    # Look for a child of a certain type.
    # Returns the child or None.
    # Raises ValueError if more than one child of the given type is found.
    children = list(filter(lambda child: isinstance(child, child_type),
                           parent.children))
    if len(children) > 1:
        raise ValueError(f"too many children found of type {child_type}")

    if children:
        return children[0]

    if must_exist:
        raise FabException(f'Could not find child of type {child_type} '
                           f'in {parent}')
    return None


class FortranAnalyserBase(ABC):
    """
    Base class for Fortran parse-tree analysers, e.g FortranAnalyser and
    X90Analyser.

    """
    _intrinsic_modules = ['iso_fortran_env', 'iso_c_binding']

    def __init__(self, config: BuildConfig,
                 result_class,
                 std: Optional[str] = None):
        """
        :param config: The BuildConfig object.
        :param result_class:
            The type (class) of the analysis result. Defined by the subclass.
        :param std:
            The Fortran standard.

        """
        self._config = config
        self.result_class = result_class
        self.f2008_parser = ParserFactory().create(std=std or "f2008")

    @property
    def config(self) -> BuildConfig:
        '''Returns the BuildConfig to use.
        '''
        return self._config

    def run(self, fpath: Path) \
            -> Union[Tuple[AnalysedDependent, Path],
                     Tuple[EmptySourceFile, None],
                     Tuple[Exception, None]]:
        """
        Parse the source file and record what we're interested in (subclass
        specific).

        Reloads previous analysis results if available.

        Returns the analysis data and the result file where it was
        stored/loaded.

        """
        # calculate the prebuild filename
        file_hash = file_checksum(fpath).file_hash
        analysis_fpath = self._get_analysis_fpath(fpath, file_hash)

        # do we already have analysis results for this file?
        if analysis_fpath.exists():
            log_or_dot(logger, f"found analysis prebuild for {fpath}")

            # Load the result file into whatever result class we use.
            loaded_result = self.result_class.load(analysis_fpath)
            if loaded_result:
                # This result might have been created by another user; their
                # prebuild folder copied to ours. If so, the fpath in the
                # result will *not* point to the file we eventually want to
                # compile, it will point to the user's original file,
                # somewhere else. So replace it with our own path.
                loaded_result.fpath = fpath
                return loaded_result, analysis_fpath

        log_or_dot(logger, f"analysing {fpath}")

        # parse the file, get a node tree
        node_tree = self._parse_file(fpath=fpath)
        if isinstance(node_tree, Exception):
            return (Exception(f"error parsing file '{fpath}':\n{node_tree}"),
                    None)
        if node_tree.content[0] is None:
            logger.debug(f"  empty tree found when parsing {fpath}")
            # todo: If we don't save the empty result we'll keep analysing
            # it every time!
            return EmptySourceFile(fpath), None

        # find things in the node tree
        analysed_file = self.walk_nodes(fpath=fpath, file_hash=file_hash,
                                        node_tree=node_tree)
        analysed_file.save(analysis_fpath)

        return analysed_file, analysis_fpath

    def _get_analysis_fpath(self, fpath, file_hash) -> Path:
        return Path(self.config.prebuild_folder /
                    f'{fpath.stem}.{file_hash}.an')

    def _parse_file(self, fpath):
        """Get a node tree from a fortran file."""
        reader = FortranFileReader(
            str(fpath),
            ignore_comments=False,
            include_omp_conditional_lines=self.config.openmp)
        # don't call sys.exit, it messes up the multi-processing
        reader.exit_on_error = False

        try:
            tree = self.f2008_parser(reader)
            return tree
        except FortranSyntaxError as err:
            # Don't return the FortranSyntaxError, it breaks multiprocessing!
            logger.error(f"\nfparser raised a syntax error in {fpath}\n{err}")
            return Exception(f"syntax error in {fpath}\n{err}")
        except Exception as err:
            logger.error(f"\nunhandled error '{type(err)}' in {fpath}\n{err}")
            return Exception(f"unhandled error '{type(err)}' in "
                             f"{fpath}\n{err}")

    @abstractmethod
    def walk_nodes(self, fpath, file_hash, node_tree) -> AnalysedDependent:
        """
        Examine the nodes in the parse tree, recording things we're
        interested in.

        Return type depends on our subclass, and will be a subclass of
        AnalysedDependent.

        """
        raise NotImplementedError
