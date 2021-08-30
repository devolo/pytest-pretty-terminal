import inspect
import re
from typing import Dict, Optional

import pytest
from _pytest.python import Function

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

def get_item_name_and_spec(nodeid: str) -> Optional[str]:
    """Split item nodeid into function name and - if existing - callspec res. parameterization."""
    tokens = nodeid.split("[", 1)
    return tokens[0].strip(), "[" + tokens[1].strip() if len(tokens) > 1 else None


def get_status_color(status: str) -> Dict[str, bool]:
    """Return (markup) color for test result status."""
    return COLORMAP.get(status, {})


def get_item_nodeid(item: Function) -> str:
    """Build item node id."""
    # note: pytest's item.nodeid could be modified by third party, so build a local one here
    if item.location and len(item.location) > 2:
        return item.location[0].replace("\\", "/") + "::" + item.location[2].replace(".", "::")
    return item.fspath.relto(item.config.rootdir).replace("\\", "/") + "::" + item.getmodpath().replace(".", "::")


def build_terminal_report(when: str, item: Function, status: str = None, step: int = None, level: int = 1):
    """Generate (pretty) terminal output.

        :param when: The call info ("setup", "call").
        :param item: The item to report.
        :param status: The status ("passed", "failed", "skipped", "blocked").
        :param item: The step index to report.
        :param level: The stack trace level (1 = the caller's level, 2 = the caller's caller level, 3 = ...).
    """
    # pylint: disable=no-member  # pylint.reporter is set in pytest_configure
    
    # extract doc string from source
    (frame, _, line, _, _) = inspect.stack()[level][0:5]
    source_list = inspect.getsourcelines(frame)
    source_code = "".join(source_list[0][line - source_list[1]:])
    docs = re.findall(r"^[\s]*\"\"\"(.*?)\"\"\"", source_code, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    doc_string = inspect.cleandoc(docs[0]) if docs else ""

    if hasattr(pytest, "reporter") and getattr(item.config.option, "pretty", False):
        if when == "setup":
            if not step:
                title, specs = get_item_name_and_spec(get_item_nodeid(item) or "")
                pytest.reporter.line("")
                pytest.reporter.write_sep("-", title, bold=True)
                pytest.reporter.write_line(inspect.cleandoc(item.obj.__doc__ or ""))
                pytest.reporter.write_line("parameterization " + specs if specs else "")
            if step and item.config.option.verbose > 1:
                pytest.reporter.write_sep("-", "Step " + str(step), bold=True)
                pytest.reporter.write(doc_string + ("\n" if doc_string else ""))
        elif when == "call":
            if not step:
                pytest.reporter.write_sep("-", bold=True)
                fill = getattr(pytest.reporter, "_tw").fullwidth - getattr(pytest.reporter, "_width_of_current_line") - 1
                pytest.reporter.write_line(status.upper().rjust(fill), **get_status_color(status))
            if step and item.config.option.verbose > 1:
                fill = getattr(pytest.reporter, "_tw").fullwidth - getattr(pytest.reporter, "_width_of_current_line") - 1
                pytest.reporter.write_line(status.upper().rjust(fill), **get_status_color(status))
    else:
        if when == "setup" and step and item.config.option.verbose > 1:
            pytest.reporter.line("")
        if when == "call" and step and item.config.option.verbose > 1:
            pytest.reporter.line(get_item_nodeid(item) + " step " + str(step) + " " + status.upper())
