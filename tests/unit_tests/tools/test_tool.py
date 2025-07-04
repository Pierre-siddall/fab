##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################

'''Tests the tool class.
'''


import logging
from pathlib import Path
from unittest import mock

import pytest

from fab.tools import Category, CompilerSuiteTool, ProfileFlags, Tool


def test_tool_constructor():
    '''Test the constructor.'''
    tool = Tool("gnu", "gfortran", Category.FORTRAN_COMPILER)
    assert str(tool) == "Tool - gnu: gfortran"
    assert tool.exec_name == "gfortran"
    assert tool.name == "gnu"
    assert tool.category == Category.FORTRAN_COMPILER
    assert isinstance(tool.logger, logging.Logger)
    assert tool.is_compiler

    linker = Tool("gnu", "gfortran", Category.LINKER)
    assert str(linker) == "Tool - gnu: gfortran"
    assert linker.exec_name == "gfortran"
    assert linker.name == "gnu"
    assert linker.category == Category.LINKER
    assert isinstance(linker.logger, logging.Logger)
    assert not linker.is_compiler

    # Check that a path is accepted
    mytool = Tool("MyTool", Path("/bin/mytool"))
    assert mytool.name == "MyTool"
    # A path should be converted to a string, since this
    # is later passed to the subprocess command
    assert mytool.exec_name == "/bin/mytool"
    assert mytool.category == Category.MISC

    # Check that if we specify no category, we get the default:
    misc = Tool("misc", "misc")
    assert misc.exec_name == "misc"
    assert misc.name == "misc"
    assert misc.category == Category.MISC


def test_tool_chance_exec_name():
    '''Test that we can change the name of the executable.
    '''
    tool = Tool("gfortran", "gfortran", Category.FORTRAN_COMPILER)
    assert tool.exec_name == "gfortran"
    tool.change_exec_name("start_me_instead")
    assert tool.exec_name == "start_me_instead"


def test_tool_is_available():
    '''Test that is_available works as expected.'''
    tool = Tool("gfortran", "gfortran", Category.FORTRAN_COMPILER)
    with mock.patch.object(tool, "check_available", return_value=True):
        assert tool.is_available
    tool._is_available = False

    # Test the exception when trying to use in a non-existent tool:
    with pytest.raises(RuntimeError) as err:
        tool.run("--ops")
    assert ("Tool 'gfortran' is not available to run '['gfortran', '--ops']'"
            in str(err.value))

    # Test setting the option and the getter
    tool = Tool("gfortran", "gfortran", Category.FORTRAN_COMPILER,
                availability_option="am_i_here")
    assert tool.availability_option == "am_i_here"

    # Test that the actual check_available function works. Return 0 to
    # indicate no error when running the tool:
    mock_result = mock.Mock(returncode=0)
    with mock.patch('fab.tools.tool.subprocess.run',
                    return_value=mock_result) as tool_run:
        assert tool.check_available()
    tool_run.assert_called_once_with(['gfortran', 'am_i_here'],
                                     capture_output=True, env=None,
                                     cwd=None, check=False)
    with mock.patch.object(tool, "run", side_effect=RuntimeError("")):
        assert not tool.check_available()


def test_tool_flags_no_profile():
    '''Test that flags without using a profile work as expected.'''
    tool = Tool("gfortran", "gfortran", Category.FORTRAN_COMPILER)
    # pylint: disable-next=use-implicit-booleaness-not-comparison
    assert tool.get_flags() == []
    tool.add_flags("-a")
    assert tool.get_flags() == ["-a"]
    tool.add_flags(["-b", "-c"])
    assert tool.get_flags() == ["-a", "-b", "-c"]


def test_tool_profiles():
    '''Test that profiles work as expected. These tests use internal
    implementation details of ProfileFlags, but we need to test that the
    exposed flag-related API works as expected

    '''
    tool = Tool("gfortran", "gfortran", Category.FORTRAN_COMPILER)
    # Make sure by default we get ProfileFlags
    assert isinstance(tool._flags, ProfileFlags)
    assert tool.get_flags() == []

    # Define a profile with no inheritance
    tool.define_profile("mode1")
    assert tool.get_flags("mode1") == []
    tool.add_flags("-flag1", "mode1")
    assert tool.get_flags("mode1") == ["-flag1"]

    # Define a profile with inheritance
    tool.define_profile("mode2", "mode1")
    assert tool.get_flags("mode2") == ["-flag1"]
    tool.add_flags("-flag2", "mode2")
    assert tool.get_flags("mode2") == ["-flag1", "-flag2"]


class TestToolRun:
    '''Test the run method of Tool.'''

    def test_no_error_no_args(self,):
        '''Test usage of `run` without any errors when no additional
        command line argument is provided.'''
        tool = Tool("gnu", "gfortran", Category.FORTRAN_COMPILER)
        mock_result = mock.Mock(returncode=0, return_value=123)
        mock_result.stdout.decode = mock.Mock(return_value="123")

        with mock.patch('fab.tools.tool.subprocess.run',
                        return_value=mock_result):
            assert tool.run(capture_output=True) == "123"
            assert tool.run(capture_output=False) == ""

    def test_no_error_with_single_args(self):
        '''Test usage of `run` without any errors when a single
        command line argument is provided as string.'''
        tool = Tool("gnu", "gfortran", Category.FORTRAN_COMPILER)
        mock_result = mock.Mock(returncode=0)
        with mock.patch('fab.tools.tool.subprocess.run',
                        return_value=mock_result) as tool_run:
            tool.run("a")
        tool_run.assert_called_once_with(
            ["gfortran", "a"], capture_output=True, env=None,
            cwd=None, check=False)

    def test_no_error_with_multiple_args(self):
        '''Test usage of `run` without any errors when more than
        one command line argument is provided as a list.'''
        tool = Tool("gnu", "gfortran", Category.FORTRAN_COMPILER)
        mock_result = mock.Mock(returncode=0)
        with mock.patch('fab.tools.tool.subprocess.run',
                        return_value=mock_result) as tool_run:
            tool.run(["a", "b"])
        tool_run.assert_called_once_with(
            ["gfortran", "a", "b"], capture_output=True, env=None,
            cwd=None, check=False)

    def test_error(self):
        '''Tests the error handling of `run`. '''
        tool = Tool("gnu", "gfortran", Category.FORTRAN_COMPILER)
        result = mock.Mock(returncode=1)
        mocked_error_message = 'mocked error message'
        result.stderr.decode = mock.Mock(return_value=mocked_error_message)
        with mock.patch('fab.tools.tool.subprocess.run',
                        return_value=result):
            with pytest.raises(RuntimeError) as err:
                tool.run()
            assert mocked_error_message in str(err.value)
            assert "Command failed with return code 1" in str(err.value)

    def test_error_file_not_found(self):
        '''Tests the error handling of `run`. '''
        tool = Tool("does_not_exist", "does_not_exist",
                    Category.FORTRAN_COMPILER)
        with mock.patch('fab.tools.tool.subprocess.run',
                        side_effect=FileNotFoundError("not found")):
            with pytest.raises(RuntimeError) as err:
                tool.run()
            assert ("Command '['does_not_exist']' could not be executed."
                    in str(err.value))


def test_suite_tool():
    '''Test the constructor.'''
    tool = CompilerSuiteTool("gnu", "gfortran", "gnu",
                             Category.FORTRAN_COMPILER)
    assert str(tool) == "CompilerSuiteTool - gnu: gfortran"
    assert tool.exec_name == "gfortran"
    assert tool.name == "gnu"
    assert tool.suite == "gnu"
    assert tool.category == Category.FORTRAN_COMPILER
    assert isinstance(tool.logger, logging.Logger)
