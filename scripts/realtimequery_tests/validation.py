import datetime
import json
import time
from collections import OrderedDict
import traceback
from log_config import log

def pretty_time() -> str:
    return str(datetime.datetime.now())[:19]

class TestResult:

    def __init__(self) -> None:
        self.errors = []
        self.successes = []
        self.warnings = []
        self.table_results = {}

    def __repr__(self):
        return "TestResults: %s" % json.dumps({"successes": self.successes, "errors": self.errors,
                                                  "warnings": list(set(self.warnings))}, indent=1)

    def __str__(self):
        return "TestResults: %s" % json.dumps({"successes": self.successes, "errors": self.errors,
                                                  "warnings": list(set(self.warnings))}, indent=1)

    def update_success(self, msg: str) -> None:
        """
        Appends success message to the test result
        :param msg: str, success message
        :return:
        """
        Time = pretty_time()
        if("%s: %s" % (Time, msg) not in self.errors):
            self.successes.append("%s: %s" % (pretty_time(), msg))
        # log.info(msg)

    def update_error(self, msg: str, skip_test: bool = False) -> None:
        """
        Appends error to the test result
        :param msg: str, error message
        :param skip_test: bool. If True it will skip the further test execution else it will continue, default is True
        :return:
        """
        Time = pretty_time()
        if("%s: %s" % (Time, msg) not in self.errors):
            self.errors.append("%s: %s" % (Time, msg))
        # log.error(msg)
        if skip_test:
            raise AssertionError(msg)

    def update_warning(self, msg: str) -> None:
        """
        Appends waring to the test result
        :param msg: str, error message
        :return:
        """
        Time = pretty_time()
        if("%s: %s" % (Time, msg) not in self.errors):
            self.warnings.append("%s: %s" % (pretty_time(), msg))
        # log.warning(msg)

    def update_exception(self, ex) -> None:
        exception = traceback.format_exc()
        ex_type = type(ex).__name__
        if ex_type != "AssertionError":
            # log.error(exception)
            self.errors.append(exception)