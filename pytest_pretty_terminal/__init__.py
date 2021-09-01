"""pytest plugin for generating prettier terminal output"""

from importlib.metadata import PackageNotFoundError, version

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.python import Function
from _pytest.runner import CallInfo
from ._helpers import build_terminal_report, get_item_name_and_spec, get_status_color
from ._pretty_terminal_reporter import PrettyTerminalReporter
try:
    __version__ = version("pytest_pretty_terminal")
except PackageNotFoundError:
    # package is not installed - e.g. pulled and run locally
    __version__ = "0.0.0"



@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Function, call: CallInfo):
    """This is called at setup, run/call and teardown of test items.

        Generates adaptavist test run results from test reports.
    """
    outcome = yield
        
    report = outcome.get_result()
    
    if hasattr(item, 'callspec'):
        report.user_properties.append(("params", item.callspec.params))
    report.user_properties.append(("docstr", item.obj.__doc__))


def enable_terminal_report(config: Config):
    """Enable terminal report."""
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
    """Patch terminal size."""

    # this function tries to fix the layout issue related to jenkins console
    terminalreporter = config.pluginmanager.getplugin("terminalreporter_2")

    if not terminalreporter:
        return

    tw = getattr(terminalreporter.tr, "_tw")

    if not tw:
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

    import shutil
    width, _ = shutil.get_terminal_size((default_width, default_height))
    tw.fullwidth = width



@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config):
    # init the terminal reporter
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
    """Add options to control plugin."""

    group = parser.getgroup("pretty-terminal")
    group.addoption("--pretty", action="store_true", dest="pretty", default=False,
                    help="Make pytest terminal output more readable (default: False)")

# @pytest.hookimpl(tryfirst=True)
# def pytest_runtest_setup(item):
#     """This is called before calling the test item (i.e. before any parameter/fixture call).

#         Used to skip test items dynamically (e.g. triggered by some other item or control function).
#     """
#     build_terminal_report(when="setup", item=item)

#     skip_status = get_marker(item, "block") or get_marker(item, "skip")

#     skip_reason = None

#     if not skip_reason and skip_status:
#         skip_reason = skip_status.kwargs.get("reason", None)
#     if not skip_reason and pytest.test_result_data[item.fullname].get("blocked", None) is True:
#         skip_reason = pytest.test_result_data[item.fullname].get("comment", None)

#     if skip_reason:
#         pytest.skip(msg=skip_reason)

# @pytest.hookimpl(hookwrapper=True, tryfirst=True)
# def pytest_runtest_makereport(item, call):
#     """This is called at setup, run/call and teardown of test items.

#         Generates adaptavist test run results from test reports.
#     """
#     outcome = yield

#     report = outcome.get_result()

#     report.item_info = {}
#     report.item_info["atmcfg"] = {"project_key": pytest.project_key, "test_environment": pytest.test_environment, "test_plan_key": pytest.test_plan_key, "test_run_key": pytest.test_run_key}
#     report.item_info["nodeid"] = get_item_nodeid(item)
#     report.item_info["docstr"] = inspect.cleandoc(item.obj.__doc__ or "")

#     skip_status = get_marker(item, "block") or get_marker(item, "skip")

#     if call.when == "setup":
#         if getattr(item.config.option, "adaptavist", False):
#             # setup report only if adaptavist reporting is enabled
#             setup_report(getattr(item.config, "workerinput", {}))
#             report.item_info["atmcfg"] = {"project_key": pytest.project_key, "test_plan_key": pytest.test_plan_key, "test_run_key": pytest.test_run_key}

#         if not call.excinfo and not skip_status and not pytest.test_result_data[item.fullname].get("blocked", None) is True:
#             # no skipped or blocked methods to report
#             return
#     elif call.when != "call":
#         return

#     # if method was blocked dynamically (during call) an appropriate marker is used
#     # to handle the reporting in the same way as for statically blocked methods
#     # (status will be reported as "Blocked" with given comment in Adaptavist)
#     if not skip_status and ((call.excinfo and call.excinfo.type in (pytest.block.Exception, pytest.skip.Exception)) or (not call.excinfo and pytest.test_result_data[item.fullname].get("blocked", None) is True)):
#         reason = pytest.test_result_data[item.fullname].get("comment", None) or (str(call.excinfo.value).partition("\n")[0] if call.excinfo and call.excinfo.type in (pytest.block.Exception, pytest.skip.Exception) else None)
#         skip_status = pytest.mark.block(reason=reason) if ((call.excinfo and call.excinfo.type is pytest.block.Exception) or pytest.test_result_data[item.fullname].get("blocked", None) is True) else pytest.mark.skip(reason=reason)
#         if report.outcome != "skipped":
#             report.outcome = "skipped"  # to mark this as SKIPPED in pytest reports
#             report.longrepr = (__file__, getattr(sys, "_getframe")().f_lineno if hasattr(sys, "_getframe") else None, f"Skipped: {reason or 'blocked dynamically or partially'}")

#     # report exceptions
#     if call.excinfo:
#         exc_info = build_exception_info(item.fullname, call.excinfo.type, call.excinfo.value, getattr(call.excinfo.traceback[-1], "_rawentry"))

#         if exc_info and exc_info not in (pytest.test_result_data[item.fullname].get("comment", None) or ""):

#             if (call.excinfo.type is not pytest.skip.Exception) and not skip_status:
#                 pytest.test_result_data[item.fullname]["comment"] = "".join((pytest.test_result_data[item.fullname].get("comment", None) or "", html_row(False, exc_info)))

#     # handling failed assumptions
#     handle_failed_assumptions(item, call, report)

#     build_report_description(item, call, report, skip_status)

#     build_terminal_report(when="call", item=item, status=report.outcome if not skip_status else ("blocked" if skip_status.name == "block" else "skipped"))

#     report.item_info["report"] = pytest.report[get_item_nodeid(item)]

#     if not getattr(item.config.option, "adaptavist", False):
#         # adaptavist reporting disabled: no need to proceed here
#         return

#     if pytest.test_result_data[item.fullname].get("done", False):
#         # this item has been reported already within a meta block context (see below)
#         return

#     marker = get_marker(item, "testcase")
#     if marker is not None:

#         test_case_key = marker.kwargs["test_case_key"]
#         test_step_key = marker.kwargs["test_step_key"]

#         _, specs = get_item_name_and_spec(get_item_nodeid(item))
#         create_report(test_case_key, test_step_key, call.stop - call.start, skip_status, report.passed, pytest.test_result_data[item.fullname], specs)
