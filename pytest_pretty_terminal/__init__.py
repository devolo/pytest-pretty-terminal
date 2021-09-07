"""pytest plugin for generating prettier terminal output"""

import logging
import shutil
from importlib.metadata import PackageNotFoundError, version

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.logging import (_LiveLoggingStreamHandler,
                             get_log_level_for_setting, get_option_ini)
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
    # pretty terminal reporting needs capturing to be turned off ("-s") to function properly
    if getattr(config.option, "pretty", False) and getattr(config.option, "capture", None) != "no":
        terminalreporter = PrettyTerminalReporter(config)
        config.pluginmanager.register(terminalreporter, "pretty_terminal_reporter")
        
        setattr(config.option, "capture", "no")
        capturemanager = config.pluginmanager.getplugin("capturemanager")
        capturemanager.stop_global_capturing()
        setattr(capturemanager, "_method", getattr(config.option, "capture"))
        capturemanager.start_global_capturing()

        terminalreporter = config.pluginmanager.getplugin("terminalreporter")
        config.pluginmanager.unregister(terminalreporter)
        
        terminalreporter.pytest_runtest_logstart = lambda nodeid, location: None
        terminalreporter.pytest_runtest_logfinish = lambda nodeid: None
        
        config.pluginmanager.register(terminalreporter, "terminalreporter")
        
        logging_plugin = config.pluginmanager.getplugin("logging-plugin")
        
        logging_plugin.log_cli_handler = _LiveLoggingStreamHandler(terminalreporter, capturemanager)
        logging_plugin.log_cli_level = get_log_level_for_setting(config, "log_cli_level", "log_level") or logging.INFO
        
        log_cli_formatter = logging_plugin._create_formatter(
            get_option_ini(config, "log_cli_format", "log_format"),
            get_option_ini(config, "log_cli_date_format", "log_date_format"),
            get_option_ini(config, "log_auto_indent"),
        )
        logging_plugin.log_cli_handler.setFormatter(log_cli_formatter)


def patch_terminal_size(config: Config):
    """
    Patch terminal size.
    this function tries to fix the layout issue related to jenkins console
    :param config: The pytest config object
    """
    terminal_reporter = config.pluginmanager.getplugin("pretty_terminal_reporter")
    terminal_writer: TerminalWriter = config.get_terminal_writer()
    
    if not terminal_reporter or not terminal_writer:
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
    patch_terminal_size(config)


def pytest_addoption(parser: Parser):
    """
    Add options to control the plugin.

    :param parser: Parser for command line arguments and ini-file values
    """
    group = parser.getgroup("pretty-terminal")
    group.addoption("--pretty", action="store_true", dest="pretty", default=False,
                    help="Make pytest terminal output more readable (default: False)")
