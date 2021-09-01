"""pytest plugin for generating prettier terminal output"""

import shutil
from importlib.metadata import PackageNotFoundError, version

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.python import Function
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from pluggy.callers import _Result
from py.io import TerminalWriter

from ._pretty_terminal_reporter import PrettyTerminalReporter

try:
    __version__ = version("pytest_pretty_terminal")
except PackageNotFoundError:
    # package is not installed - e.g. pulled and run locally
    __version__ = "0.0.0"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Function, call: CallInfo):  # pylint: disable=unused-argument
    """
    This is called at setup, run/call and teardown of test items.
    Collects used parameter and test's docstrings.

    :param item: A Function item
    :param call: The CallInfo for the phase
    """
    outcome: _Result = yield
    report: TestReport = outcome.get_result()
    if hasattr(item, 'callspec'):
        report.user_properties.append(("params", item.callspec.params))
    report.user_properties.append(("docstr", item.obj.__doc__))


def enable_terminal_report(config: Config):
    """
    Enable terminal reporting.

    :param config: The pytest config object
    """
    terminalreporter = PrettyTerminalReporter(config)
    config.pluginmanager.register(terminalreporter, "pretty_terminal_reporter")
    pytest.reporter = config.pluginmanager.getplugin("pretty_terminal_reporter")

    # pretty terminal reporting needs capturing to be turned off ("-s") to function properly
    if getattr(config.option, "pretty", False) and getattr(config.option, "capture", None) != "no":
        setattr(config.option, "capture", "no")
        capturemanager = config.pluginmanager.getplugin("capturemanager")
        capturemanager.stop_global_capturing()
        setattr(capturemanager, "_method", getattr(config.option, "capture"))
        capturemanager.start_global_capturing()


def patch_terminal_size(config: Config):
    """
    Patch terminal size.

    :param config: The pytest config object
    """

    # this function tries to fix the layout issue related to jenkins console
    terminalreporter = config.pluginmanager.getplugin("pretty_terminal_reporter")
    if not terminalreporter:
        return

    terminal_writer: TerminalWriter = config.get_terminal_writer()
    if not terminal_writer:
        return

    try:
        # calculate terminal size from screen dimension (e.g. 1920 -> 192)
        import tkinter
        default_width = min(192, int((tkinter.Tk().winfo_screenwidth() + 9) / 10))
        default_height = int((tkinter.Tk().winfo_screenheight() + 19) / 20)
    except Exception:  # pylint: disable=broad-except
        # tradeoff
        default_width = 152
        default_height = 24

    width, _ = shutil.get_terminal_size((default_width, default_height))
    terminal_writer.fullwidth = width


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config):
    """
    Perform initial configuration.

    :param config: The pytest config object
    """
    if not hasattr(config, "workerinput"):
        enable_terminal_report(config)
        if pytest.reporter:
            pytest.reporter.tr.section("ATM build meta data", bold=True)
            pytest.reporter.tr.line("build_usr: %s" % ("build_usr" or "unknown"))
    patch_terminal_size(config)


def import_module(module_name: str):
    """Import and return module if existing."""

    try:
        return pytest.importorskip(module_name)
    except pytest.skip.Exception:
        return None

# if import_module("xdist"):
#     @pytest.hookimpl(trylast=True)
#     def pytest_configure_node(node: "WorkerController"):
#         """This is called in case of using xdist to pass data to worker nodes."""
#         node.workerinput["options"] = {
#             "dist": node.config.option.dist,
#             "numprocesses": node.config.option.numprocesses
#         }


def pytest_addoption(parser: Parser):
    """
    Add options to control the plugin.

    :param parser: Parser for command line arguments and ini-file values
    """
    group = parser.getgroup("pretty-terminal")
    group.addoption("--pretty", action="store_true", dest="pretty", default=False,
                    help="Make pytest terminal output more readable (default: False)")
