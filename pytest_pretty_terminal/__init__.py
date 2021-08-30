import shutil
from typing import Dict

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.python import Function
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from ._helpers import build_terminal_report, get_item_name_and_spec, get_status_color

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version  # type: ignore

try:
    __version__ = version("pytest_pretty_terminal")
except PackageNotFoundError:
    # package is not installed - e.g. pulled and run locally
    __version__ = "0.0.0"


class Logreport:
    def __init__(self, config: Config):
        pytest.report = {}
        self.config = config
        self.terminalreporter: TerminalReporter = config.pluginmanager.getplugin("terminalreporter")


    def pytest_runtest_logreport(self, report: TestReport):
        """Empty log in pretty mode (will be done during execution, see calls of build_terminal_report())."""
        item_info: Dict = getattr(report, "item_info", {})
        worker_node_suffix = f" [{' -> '.join(filter(None, (report.node.gateway.id, item_info['atmcfg'].get('test_environment', None))))}]" if getattr(self.config.option, "dist", None) == "each" and getattr(report, "node") else ""

        if item_info.get("report", {}):
            pytest.report.update({(item_info.get("nodeid") or "") + worker_node_suffix: item_info.get("report", {})})

        category, _, _ = self.config.hook.pytest_report_teststatus(report=report, config=self.config)
        self.terminalreporter.stats.setdefault(category, []).append(report)  # needed for statistics and summary

        if not getattr(self.config.option, "numprocesses", 0) or report.when == "teardown":
            # in sequential mode terminal output is produced immediately (see build_terminal_report)
            return

        if report.when == "setup":
            if (getattr(self.config.option, "numprocesses", 0) or 0) < 2:
                title, specs = get_item_name_and_spec(item_info.get("nodeid") or "")
                self.terminalreporter.line("")
                self.terminalreporter.write_sep("-", title, bold=True)
                self.terminalreporter.write_line(item_info.get("docstr") or "")
                self.terminalreporter.write_line("parameterization " + specs if specs else "")

            if not report.skipped:
                return

        if (getattr(self.config.option, "numprocesses", 0) or 0) > 1:
            title, specs = get_item_name_and_spec(item_info.get("nodeid") or "")
            self.terminalreporter.line("")
            self.terminalreporter.write_sep("-", title + worker_node_suffix, bold=True)
            self.terminalreporter.write_line(item_info.get("docstr") or "")
            self.terminalreporter.write_line("parameterization " + specs if specs else "")

        status = item_info.get("report", {}).get("status") or category

        self.terminalreporter.write_sep("-", bold=True)
        fill = getattr(self.terminalreporter, "_tw").fullwidth - getattr(self.terminalreporter, "_width_of_current_line") - 1
        self.terminalreporter.write_line(status.upper().rjust(fill), **get_status_color(status))


def enable_terminal_report(config: Config):
    """Enable terminal report."""

    # pretty terminal reporting needs capturing to be turned off ("-s") to function properly
    if (
        getattr(config.option, "pretty", False)
        and getattr(config.option, "capture", None) != "no"
    ):
        setattr(config.option, "capture", "no")
        capturemanager = config.pluginmanager.getplugin("capturemanager")
        capturemanager.stop_global_capturing()
        setattr(capturemanager, "_method", getattr(config.option, "capture"))
        capturemanager.start_global_capturing()


def patch_terminal_size(config: Config):
    """Patch terminal size."""

    # this function tries to fix the layout issue related to jenkins console
    terminalreporter = config.pluginmanager.getplugin("terminalreporter")

    if not terminalreporter or not terminalreporter._tw:
        return

    try:
        # calculate terminal size from screen dimension (e.g. 1920 -> 192)
        import tkinter  # pylint: disable=import-outside-toplevel
        default_width = min(192, int((tkinter.Tk().winfo_screenwidth() + 9) / 10))
        default_height = int((tkinter.Tk().winfo_screenheight() + 19) / 20)
    except Exception:  # pylint: disable=broad-except
        # tradeoff
        default_width = 152
        default_height = 24

    width, _ = shutil.get_terminal_size((default_width, default_height))
    terminalreporter._tw.fullwidth = width

@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config):
    """Prepare and start logging/reporting (called at the beginning of the test process)."""
    # init the terminal reporter
    pytest.reporter = config.pluginmanager.getplugin("terminalreporter")

    config.pluginmanager.register(Logreport(config), "pretty_terminal")

    if not hasattr(config, "workerinput"):
        enable_terminal_report(config)

    patch_terminal_size(config)

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: Function):
    """This is called before calling the test item (i.e. before any parameter/fixture call).

        Used to skip test items dynamically (e.g. triggered by some other item or control function).
    """
    build_terminal_report(when="setup", item=item)

def pytest_addoption(parser: Parser):
    """Add options to control plugin."""

    group = parser.getgroup("pretty-terminal")

    group.addoption("--pretty", action="store_true", dest="pretty", default=False,
                    help="Make pytest terminal output more readable (default: False)")
