"""Terminal reporter module"""

from typing import Optional, Tuple

import pytest
from _pytest.config import Config
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from ._helpers import get_item_name_and_spec, get_status_color


class PrettyTerminalReporter:
    """
    Terminal reporter class used for prettifying terminal output (also used for synchronization of xdist-worker nodes).

    :param config: The pytest config object
    """

    def __init__(self, config: Config):
        """Constructor"""

        # dictionary to store final report
        pytest.report = {}
        self.config = config
        self.terminal_reporter: TerminalReporter = config.pluginmanager.getplugin("terminalreporter")
        self.terminal_reporter.showfspath = False

    def pytest_runtest_logreport(self, report: TestReport):

        item_info = getattr(report, "item_info", {})
        user_properties = dict(report.user_properties)
        worker_node_suffix = f" [{' -> '.join(filter(None, (report.node.gateway.id, item_info['atmcfg'].get('test_environment', None))))}]" \
            if getattr(self.config.option, "dist", None) == "each" and getattr(report, "node") \
            else ""

        if item_info.get("atmcfg", None):
            pytest.project_key = item_info["atmcfg"].get("project_key", None)
            pytest.test_plan_key = item_info["atmcfg"].get("test_plan_key", None)
            pytest.test_run_key = item_info["atmcfg"].get("test_run_key", None)
            if not hasattr(pytest, "test_run_keys"):
                pytest.test_run_keys = []
            if pytest.test_run_key and pytest.test_run_key not in pytest.test_run_keys:
                pytest.test_run_keys.append(pytest.test_run_key)

        if item_info.get("report", {}):
            pytest.report.update({(item_info.get("nodeid", None) or "") + worker_node_suffix: item_info.get("report", {})})

        if not getattr(self.config.option, "pretty", False):
            return

        if report.when == "teardown":
            return

        if report.when == "setup":
            if (getattr(self.config.option, "numprocesses", 0) or 0) < 2:
                title, _ = get_item_name_and_spec(report.nodeid)
                self.terminal_reporter.line("")
                self.terminal_reporter.write_sep("-", title, bold=True)
                self.terminal_reporter.write_line(user_properties["docstr"] or "")
                for parameter, value in user_properties.get("params", {}).items():
                    self.terminal_reporter.write_line(f"Parameterization: {parameter}={value}")

            if not report.skipped:
                return

        if (getattr(self.config.option, "numprocesses", 0) or 0) > 1:
            title, _ = get_item_name_and_spec(report.nodeid)
            self.terminal_reporter.line("")
            self.terminal_reporter.write_sep("-", title + worker_node_suffix, bold=True)
            self.terminal_reporter.write_line(user_properties["docstr"] or "")
            for parameter, value in report.user_properties.get("params", {}).items():
                self.terminal_reporter.write_line(f"Parameterization: {parameter}={value}")

        self.terminal_reporter.write_sep("-", bold=True)
        fill = getattr(self.terminal_reporter, "_tw").fullwidth - getattr(self.terminal_reporter, "_width_of_current_line") - 1
        self.terminal_reporter.write_line(report.outcome.upper().rjust(fill), **get_status_color(report.outcome))

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
            return outcome, "", outcome.upper()
        return None
        