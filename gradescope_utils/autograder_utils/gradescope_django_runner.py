from gradescope_utils.autograder_utils.json_test_runner import JSONTestRunner
from django.test.runner import DiscoverRunner
from django.conf import settings


class GradescopeDjangoRunner(DiscoverRunner):
    """Replacing Django Default Unit Test Runner with Gradescope Test Runner"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kwargs = getattr(settings, "GRADESCOPE_PARAMETERS", {})
        self.test_runner = JSONTestRunner(**kwargs)

    def run_suite(self, suite, **kwargs):
        return self.test_runner.run(suite)
