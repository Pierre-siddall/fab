##############################################################################
# (c) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT
# which you should have received as part of this distribution
##############################################################################

'''This module tests the ToolRepository.
'''

from unittest import mock
import pytest

from fab.tools import (Ar, Category, FortranCompiler, Gcc, Gfortran, Ifort,
                       Mpif90, ToolRepository)


def test_tool_repository_get_singleton_new():
    '''Tests the singleton behaviour.'''
    ToolRepository._singleton = None
    tr1 = ToolRepository()
    tr2 = ToolRepository()
    assert tr1 == tr2
    ToolRepository._singleton = None
    tr3 = ToolRepository()
    assert tr1 is not tr3


def test_tool_repository_constructor():
    '''Tests the ToolRepository constructor.'''
    tr = ToolRepository()
    assert Category.C_COMPILER in tr
    assert Category.FORTRAN_COMPILER in tr


def test_tool_repository_get_tool():
    '''Tests get_tool.'''
    tr = ToolRepository()
    gfortran = tr.get_tool(Category.FORTRAN_COMPILER, "gfortran")
    assert isinstance(gfortran, Gfortran)

    ifort = tr.get_tool(Category.FORTRAN_COMPILER, "ifort")
    assert isinstance(ifort, Ifort)


def test_tool_repository_get_tool_with_exec_name(mock_fortran_compiler):
    '''Tests get_tool when the name of the executable is specified, e.g.
    mpif90 (instead of the Fab name mpif90-gfortran etc).

    '''
    tr = ToolRepository()
    # Keep a copy of gfortran for later
    gfortran = tr.get_tool(Category.FORTRAN_COMPILER, "gfortran")

    # First add just one unavailable Fortran compiler and an mpif90 wrapper:
    tr[Category.FORTRAN_COMPILER] = []
    tr.add_tool(mock_fortran_compiler)
    mpif90 = Mpif90(mock_fortran_compiler)
    tr.add_tool(mpif90)

    # If mpif90 is not available, an error is raised:
    mpif90._is_available = False
    try:
        tr.get_tool(Category.FORTRAN_COMPILER, "mpif90")
    except KeyError as err:
        assert "Unknown tool 'mpif90' in category" in str(err)

    # When using the exec name, the compiler must be available:
    mpif90._is_available = True
    f90 = tr.get_tool(Category.FORTRAN_COMPILER, "mpif90")
    assert f90 is mpif90

    # Now add mpif90-gfortran, set mpif90-gfortran as available,
    # and mpif90-mock-fortran as unavailable. We need to make sure
    # we then get mpif90-gfortran:
    mpif90_gfortran = Mpif90(gfortran)
    tr.add_tool(mpif90_gfortran)
    mpif90._is_available = False
    mpif90_gfortran._is_available = True
    f90 = tr.get_tool(Category.FORTRAN_COMPILER, "mpif90")
    assert f90 is mpif90_gfortran

    # Then verify using the full path
    f90 = tr.get_tool(Category.FORTRAN_COMPILER, "/some/where/mpif90")
    assert f90 is mpif90_gfortran
    assert f90._full_path == "/some/where/mpif90"
    # Reset the repository, since this test messed up the compilers.
    ToolRepository._singleton = None


def test_tool_repository_get_tool_error():
    '''Tests error handling during get_tool.'''
    tr = ToolRepository()
    with pytest.raises(KeyError) as err:
        tr.get_tool("unknown-category", "something")
    assert "Unknown category 'unknown-category'" in str(err.value)

    with pytest.raises(KeyError) as err:
        tr.get_tool(Category.C_COMPILER, "something")
    assert ("Unknown tool 'something' in category 'C_COMPILER'"
            in str(err.value))


def test_tool_repository_get_default():
    '''Tests get_default.'''
    tr = ToolRepository()
    gfortran = tr.get_default(Category.FORTRAN_COMPILER, mpi=False,
                              openmp=False)
    assert isinstance(gfortran, Gfortran)

    gcc = tr.get_default(Category.C_COMPILER, mpi=False, openmp=False)
    assert isinstance(gcc, Gcc)

    # Test a non-compiler
    ar = tr.get_default(Category.AR)
    assert isinstance(ar, Ar)


def test_tool_repository_get_default_error_invalid_category():
    '''Tests error handling in get_default, the category
    must be a Category, not e.g. a string.'''
    tr = ToolRepository()
    with pytest.raises(RuntimeError) as err:
        tr.get_default("unknown-category-type")
    assert "Invalid category type 'str'." in str(err.value)


def test_tool_repository_get_default_error_missing_mpi():
    '''Tests error handling in get_default when the optional MPI
    parameter is missing (which is required for a compiler).'''
    tr = ToolRepository()
    with pytest.raises(RuntimeError) as err:
        tr.get_default(Category.FORTRAN_COMPILER, openmp=True)
    assert ("Invalid or missing mpi specification for 'FORTRAN_COMPILER'"
            in str(err.value))
    with pytest.raises(RuntimeError) as err:
        tr.get_default(Category.FORTRAN_COMPILER, mpi="123")
    assert ("Invalid or missing mpi specification for 'FORTRAN_COMPILER'"
            in str(err.value))


def test_tool_repository_get_default_error_missing_openmp():
    '''Tests error handling in get_default when the optional openmp
    parameter is missing (which is required for a compiler).'''
    tr = ToolRepository()
    with pytest.raises(RuntimeError) as err:
        tr.get_default(Category.FORTRAN_COMPILER, mpi=True)
    assert ("Invalid or missing openmp specification for 'FORTRAN_COMPILER'"
            in str(err.value))
    with pytest.raises(RuntimeError) as err:
        tr.get_default(Category.FORTRAN_COMPILER, mpi=True, openmp="123")
    assert ("Invalid or missing openmp specification for 'FORTRAN_COMPILER'"
            in str(err.value))


@pytest.mark.parametrize("mpi, openmp, message",
                         [(False, False, "any 'FORTRAN_COMPILER'."),
                          (False, True,
                           "'FORTRAN_COMPILER' that supports OpenMP"),
                          (True, False,
                           "'FORTRAN_COMPILER' that supports MPI"),
                          (True, True, "'FORTRAN_COMPILER' that supports MPI "
                                       "and OpenMP.")])
def test_tool_repository_get_default_error_missing_compiler(mpi, openmp,
                                                            message):
    '''Tests error handling in get_default when there is no compiler
    that fulfils the requirements with regards to OpenMP and MPI.'''
    tr = ToolRepository()
    with mock.patch.dict(tr, {Category.FORTRAN_COMPILER: []}), \
            pytest.raises(RuntimeError) as err:
        tr.get_default(Category.FORTRAN_COMPILER, mpi=mpi, openmp=openmp)

    assert f"Could not find {message}" in str(err.value)


def test_tool_repository_get_default_error_missing_openmp_compiler():
    '''Tests error handling in get_default when there is a compiler, but it
    does not support OpenMP (which triggers additional tests in the
    ToolRepository.'''
    tr = ToolRepository()
    fc = FortranCompiler("gfortran", "gfortran", "gnu", openmp_flag=None,
                         module_folder_flag="-J", version_regex=None)

    with mock.patch.dict(tr, {Category.FORTRAN_COMPILER: [fc]}), \
            pytest.raises(RuntimeError) as err:
        tr.get_default(Category.FORTRAN_COMPILER, mpi=False, openmp=True)

    assert ("Could not find 'FORTRAN_COMPILER' that supports OpenMP."
            in str(err.value))


def test_tool_repository_default_compiler_suite():
    '''Tests the setting of default suite for compiler and linker.'''
    tr = ToolRepository()
    tr.set_default_compiler_suite("gnu")

    # Mark all compiler and linker as available.
    with mock.patch('fab.tools.tool.Tool.is_available',
                    new_callable=mock.PropertyMock) as is_available:
        is_available.return_value = True
        for cat in [Category.C_COMPILER, Category.FORTRAN_COMPILER,
                    Category.LINKER]:
            def_tool = tr.get_default(cat, mpi=False, openmp=False)
            assert def_tool.suite == "gnu"

        tr.set_default_compiler_suite("intel-classic")
        for cat in [Category.C_COMPILER, Category.FORTRAN_COMPILER,
                    Category.LINKER]:
            def_tool = tr.get_default(cat, mpi=False, openmp=False)
            assert def_tool.suite == "intel-classic"
        with pytest.raises(RuntimeError) as err:
            tr.set_default_compiler_suite("does-not-exist")
        assert ("Cannot find 'FORTRAN_COMPILER' in the suite 'does-not-exist'"
                in str(err.value))


def test_tool_repository_no_tool_available():
    '''Tests error handling if no tool is available.'''

    tr = ToolRepository()
    tr.set_default_compiler_suite("gnu")
    with mock.patch('fab.tools.tool.Tool.is_available',
                    new_callable=mock.PropertyMock) as is_available:
        is_available.return_value = False
        with pytest.raises(RuntimeError) as err:
            tr.get_default(Category.SHELL)
        assert ("Can't find available 'SHELL' tool. Tools are 'sh'"
                in str(err.value))


def test_tool_repository_full_path():
    '''Tests that a user can request a tool with a full path,
    in which case the right tool should be returned with an updated
    exec name that uses the path.
    '''
    tr = ToolRepository()
    gfortran = tr.get_tool(Category.FORTRAN_COMPILER, "/usr/bin/gfortran")
    assert isinstance(gfortran, Gfortran)
    assert gfortran.name == "gfortran"
    assert gfortran.exec_name == "/usr/bin/gfortran"

    # Also make sure this name is indeed used when calling the compiler:
    mock_result = mock.Mock(returncode=0)
    with mock.patch('fab.tools.tool.subprocess.run',
                    return_value=mock_result) as tool_run:
        gfortran.run("a")
    tool_run.assert_called_once_with(
        ["/usr/bin/gfortran", "a"], capture_output=True, env=None,
        cwd=None, check=False)
