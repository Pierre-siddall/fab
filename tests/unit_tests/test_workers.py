#!/usr/bin/env python3

"""
Unit tests for the fab.workers module
"""

from fab.workers import WorkerPool


class TestWorkerPool:
    """Tests for the WorkerPool class."""

    @staticmethod
    def func(x):
        """Test function to multiple a value by ten."""
        return x * 10

    def test_empty(self):
        """Test of empty work list."""

        pool = WorkerPool(2)
        result = pool(self.func, [], "Test")
        assert result == ()

    def test_pool(self):
        """Test of vanilla WorkerPool."""

        pool = WorkerPool(2)
        result = pool(self.func, [1, 2, 3, 4], "Test")
        assert result == (10, 20, 30, 40)

    def test_quiet_pool(self):
        """Test of WorkerPool in quiet mode."""

        WorkerPool.quiet = True
        pool = WorkerPool(2)
        result = pool(self.func, [1, 2, 3, 4], "Test")
        WorkerPool.quiet = False
        assert result == (10, 20, 30, 40)

    def test_pool_callbacks(self):
        """Test WorkerPool with a callback function."""

        output = []

        def callback(result):
            output.append(result)

        pool = WorkerPool(2)
        pool(self.func, [1, 2, 3, 4], "Test", callback=callback)
        assert sorted(output) == [10, 20, 30, 40]
