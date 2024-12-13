# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''This module contains a few complete Fortran compilation tests. They require
a working Fortran compiler to be available.
'''

import subprocess
from pathlib import Path
from unittest import mock

from fab.artefacts import ArtefactSet
from fab.build_config import BuildConfig
from fab.steps.analyse import analyse
from fab.steps.compile_fortran import compile_fortran
from fab.steps.find_source_files import find_source_files
from fab.steps.grab.folder import grab_folder
from fab.steps.link import link_exe
from fab.steps.preprocess import preprocess_fortran
from fab.tools import ToolBox

import pytest

PROJECT_SOURCE = Path(__file__).parent / 'project-source'


def test_minimal_fortran(tmp_path):
    '''Tests a minimal hello world build with a single Fortran
    compilation pass.'''

    # build
    with BuildConfig(fab_workspace=tmp_path, tool_box=ToolBox(),
                     project_label='foo', multiprocessing=False) as config:
        grab_folder(config, PROJECT_SOURCE)
        find_source_files(config)
        preprocess_fortran(config)
        analyse(config, root_symbol='test')
        with pytest.warns(UserWarning, match="Removing managed flag"):
            compile_fortran(config, common_flags=['-c'])
        link_exe(config, flags=['-lgfortran'])

    assert len(config.artefact_store[ArtefactSet.EXECUTABLES]) == 1

    # run
    command = [str(list(config.artefact_store[ArtefactSet.EXECUTABLES])[0])]
    res = subprocess.run(command, capture_output=True, check=True)
    output = res.stdout.decode()
    assert output.strip() == 'Hello world!'


def test_minimal_fortran_two_stage(tmp_path, caplog):
    '''Tests a minimal hello world build with two Fortran
    compilation passes.'''

    # build
    with BuildConfig(fab_workspace=tmp_path, tool_box=ToolBox(),
                     project_label='foo', multiprocessing=False,
                     two_stage=True,
                     ) as config:
        grab_folder(config, PROJECT_SOURCE)
        find_source_files(config)
        preprocess_fortran(config)
        analyse(config, root_symbol='test')
        with pytest.warns(UserWarning, match="Removing managed flag"):
            compile_fortran(config, common_flags=['-c'])
        link_exe(config, flags=['-lgfortran'])

    # Check that we get the information that this is a two stage compilation
    assert ("Starting two-stage compile: mod files, multiple passes"
            in caplog.text)
    assert ("Finalising two-stage compile: object files, single pass"
            in caplog.text)
    assert "stage 2 compiled 1 files" in caplog.text

    assert len(config.artefact_store[ArtefactSet.EXECUTABLES]) == 1

    # run
    command = [str(list(config.artefact_store[ArtefactSet.EXECUTABLES])[0])]
    res = subprocess.run(command, capture_output=True, check=True)
    output = res.stdout.decode()
    assert output.strip() == 'Hello world!'


def test_minimal_fortran_error_in_stage_two(tmp_path):
    '''Test a build, but simulate a compilation error in the second
    stage. Make sure this gets properly flagged.
    '''

    with BuildConfig(fab_workspace=tmp_path, tool_box=ToolBox(),
                     project_label='foo', multiprocessing=False,
                     two_stage=True,
                     ) as config:
        grab_folder(config, PROJECT_SOURCE)
        find_source_files(config)
        preprocess_fortran(config)
        analyse(config, root_symbol='test')

        # Raise an exception the second time compile_file is called,
        # which is in the second stage
        mock_compile_file = \
            mock.patch('fab.steps.compile_fortran.compile_file',
                       side_effect=[("a", "b"), Exception("ERROR")])

        with mock_compile_file:
            with pytest.raises(RuntimeError) as err:
                compile_fortran(config, common_flags=['-c'])

    assert "Error compiling" in str(err.value)
