"""Test basic functionality of the plugin."""

import pytest

pytest_plugins = ("pytester",)


def test_fail(pytester: pytest.Pytester):
    """Test correct behavior of a failing test case."""
    pytester.makepyfile(
        """
        import pytest

        def test_a():
            assert False
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("FAILED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["failed"] == 1
    assert len(outcome) == 1


def test_pass(pytester: pytest.Pytester):
    """Test correct behavior of a passing test case."""
    pytester.makepyfile(
        """
        import pytest

        def test_a():
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("PASSED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["passed"] == 1
    assert len(outcome) == 1


def test_xfail(pytester: pytest.Pytester):
    """Test correct behavior of an expected failing test case."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.xfail
        def test_a():
            assert False
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("XFAILED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["xfailed"] == 1
    assert len(outcome) == 1


def test_xpass(pytester: pytest.Pytester):
    """Test correct behavior of an unintended passing test case."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.xfail
        def test_a():
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("XPASSED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["xpassed"] == 1
    assert len(outcome) == 1


def test_skip(pytester: pytest.Pytester):
    """Test correct behavior of a test case skipped by marker."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.skip
        def test_a():
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("SKIPPED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["skipped"] == 1
    assert len(outcome) == 1


def test_skip_inside(pytester: pytest.Pytester):
    """Test correct behavior of a test case skipped by call."""
    pytester.makepyfile(
        """
        import pytest

        def test_a():
            pytest.skip()
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("SKIPPED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["skipped"] == 1
    assert len(outcome) == 1


def test_block(pytester: pytest.Pytester):
    """Test correct behavior of a test case blocked by marker (needs pytest-adaptavist)."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.block
        def test_a():
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("BLOCKED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["blocked"] == 1
    assert len(outcome) == 1


def test_block_inside(pytester: pytest.Pytester):
    """Test correct behavior of a test case blocked by marker (needs pytest-adaptavist)."""
    pytester.makepyfile(
        """
        import pytest

        def test_a():
            pytest.block()
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("BLOCKED" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["blocked"] == 1
    assert len(outcome) == 1


def test_error_setup(pytester: pytest.Pytester):
    """Test correct behavior of a setup error."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def b():
            raise ValueError

        def test_a(b):
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("ERROR" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["errors"] == 1
    assert len(outcome) == 1


def test_error_teardown(pytester: pytest.Pytester):
    """Test correct behavior of a teardown error."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def b():
            yield
            raise ValueError

        def test_a(b):
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("ERROR" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert outcome["errors"] == 1
    assert len(outcome) == 2  # The test_a is marked as passed, but in teardown marked as error. This is default behaviour


def test_all_tests_cases_together(pytester: pytest.Pytester):
    """Test correct counting of test case outcomes."""
    pytester.makepyfile(
        """
        import pytest

        def test_a():
            assert False

        def test_b():
            assert True

        @pytest.mark.xfail
        def test_c():
            assert False

        @pytest.mark.xfail
        def test_d():
            assert True

        @pytest.mark.skip
        def test_e():
            assert True

        def test_f():
            pytest.skip()
            assert True

        @pytest.mark.block
        def test_g():
            assert True

        def test_h():
            pytest.block()
            assert True

        @pytest.fixture
        def i_fixture():
            raise ValueError

        def test_i(i_fixture):
            assert True

        @pytest.fixture
        def j_fixture():
            yield
            raise ValueError

        def test_j(j_fixture):
            assert True
        """
    )
    outcome = pytester.runpytest("--pretty").parseoutcomes()
    assert outcome["failed"] == 1
    assert outcome["passed"] == 2
    assert outcome["skipped"] == 2
    assert outcome["xfailed"] == 1
    assert outcome["xpassed"] == 1
    assert outcome["errors"] == 2
    assert outcome["blocked"] == 2


def test_parametrized_test(pytester: pytest.Pytester):
    """Test output of parameters."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize("param_a", [True, False])
        def test_a(param_a):
            assert True
        """
    )
    runtest = pytester.runpytest("--pretty")
    assert any("Parameterization: param_a = True" in line for line in runtest.outlines)
    assert any("Parameterization: param_a = False" in line for line in runtest.outlines)
    outcome = runtest.parseoutcomes()
    assert len(outcome) == 1
