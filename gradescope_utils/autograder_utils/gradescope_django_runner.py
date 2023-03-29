import sys
from gradescope_utils.autograder_utils.json_test_runner import JSONTestRunner
from django.test.runner import DiscoverRunner
from django.conf import settings


class GradescopeDjangoRunner(DiscoverRunner):
    """Replacing Django Default Unit Test Runner with Gradescope Test Runner"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_runner = None

    def get_gradescope_runner_kwargs(self):
        return getattr(settings, "GRADESCOPE_PARAMETERS", {})

    def run_suite(self, suite):
        kwargs = self.get_gradescope_runner_kwargs()
        self.test_runner = JSONTestRunner(**kwargs)
        return self.test_runner.run(suite)

