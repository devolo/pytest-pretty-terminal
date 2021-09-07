"""Terminal reporter module"""

from typing import Any, Dict, Optional, Tuple

import pytest
from _pytest.config import Config
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter


COLORMAP = {
    "passed": {
        "green": True, "bold": True
    },
    "failed": {
        "red": True, "bold": True
    },
    "blocked": {
        "blue": True, "bold": True
    },
    "skipped": {
        "yellow": True, "bold": True
    }
}


class PrettyTerminalReporter:
    """
    Terminal reporter class used for prettifying terminal output (also used for synchronization of xdist-worker nodes).

    :param config: The pytest config object
    """

    def __init__(self, config: Config):
        """Constructor"""
        self.config = config
        self.terminal_reporter: TerminalReporter = config.pluginmanager.getplugin("terminalreporter")
        self.terminal_reporter.showfspath = False

    def pytest_runtest_logreport(self, report: TestReport):
        """
        Process the test report.

        :param report: The report object to be processed
        """
        if not getattr(self.config.option, "pretty", False) or report.when == "teardown":
            return

        user_properties = dict(report.user_properties)
        worker_node_suffix = ""
        if getattr(report, "node", None):
            worker_node_suffix = " --> " + report.node.gateway.id

        title = report.nodeid.split("[", 1)[0].strip() + worker_node_suffix

        if report.when == "setup":
            if (getattr(self.config.option, "numprocesses", 0) or 0) < 2:
                self._print_docstring_and_params(title, user_properties)

            if not report.skipped:
                return

        if (getattr(self.config.option, "numprocesses", 0) or 0) > 1:
            self._print_docstring_and_params(title, user_properties)

        self.terminal_reporter.write_sep("-", bold=True)
        fill = getattr(self.terminal_reporter, "_tw").fullwidth - getattr(self.terminal_reporter, "_width_of_current_line") - 1
        self.terminal_reporter.write_line(report.outcome.upper().rjust(fill), **COLORMAP.get(report.outcome, {}))

    @pytest.hookimpl(tryfirst=True)
    def pytest_report_teststatus(self, report: TestReport) -> Optional[Tuple[str, str, str]]:
        """
        Return result-category, shortletter and verbose word for status reporting.
        In our case, the shortletter shall always be empty.

        :param report: The report object whose status is to be returned
        """
        if getattr(self.config.option, "pretty", False):
            outcome: str = report.outcome
            if report.when in ("collect", "setup", "teardown"):
                if outcome == "failed":
                    outcome = "error"
                elif not report.skipped:
                    outcome = ""
            return outcome, "", ""
        return None

    def _print_docstring_and_params(self, title: str, user_properties: Dict[str, Any]):
        """Print docstring and parameters of a test case."""
        self.terminal_reporter.line("")
        self.terminal_reporter.write_sep("-", title, bold=True)
        self.terminal_reporter.write_line(user_properties["docstr"] or "")
        for parameter, value in user_properties.get("params", {}).items():
            self.terminal_reporter.write_line(f"Parameterization: {parameter} = {value}")
