"""Running tests"""
from __future__ import print_function

import sys
import time
import json

from unittest import result
from unittest.signals import registerResult


class JSONTestResult(result.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by JSONTestRunner.
    """
    def __init__(self, stream, descriptions, verbosity, results, leaderboard,
                 failure_prefix):
        super(JSONTestResult, self).__init__(stream, descriptions, verbosity)
        self.descriptions = descriptions
        self.results = results
        self.leaderboard = leaderboard
        self.failure_prefix = failure_prefix

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return doc_first_line
        else:
            return str(test)

    def getTags(self, test):
        return getattr(getattr(test, test._testMethodName), '__tags__', None)

    def getWeight(self, test):
        return getattr(getattr(test, test._testMethodName), '__weight__', None)

    def getScore(self, test):
        return getattr(getattr(test, test._testMethodName), '__score__', None)

    def getNumber(self, test):
        return getattr(getattr(test, test._testMethodName), '__number__', None)

    def getVisibility(self, test):
        return getattr(getattr(test, test._testMethodName), '__visibility__', None)

    def getHideErrors(self, test):
        return getattr(getattr(test, test._testMethodName), '__hide_errors__', None)
    
    def getMergeSubtests(self, test):
        return getattr(getattr(test, test._testMethodName), '__merge_subtests__', None)

    def getLeaderboardData(self, test):
        column_name = getattr(getattr(test, test._testMethodName), '__leaderboard_column__', None)
        sort_order = getattr(getattr(test, test._testMethodName), '__leaderboard_sort_order__', None)
        value = getattr(getattr(test, test._testMethodName), '__leaderboard_value__', None)
        return (column_name, sort_order, value)

    def startTest(self, test):
        super(JSONTestResult, self).startTest(test)

    def getOutput(self):
        if self.buffer:
            out = self._stdout_buffer.getvalue()
            err = self._stderr_buffer.getvalue()
            if err:
                if not out.endswith('\n'):
                    out += '\n'
                out += err
            return out

    def buildResult(self, test, err=None):
        failed = err is not None
        weight = self.getWeight(test)
        tags = self.getTags(test)
        number = self.getNumber(test)
        visibility = self.getVisibility(test)
        hide_errors_message = self.getHideErrors(test)
        score = self.getScore(test)
        output = self.getOutput() or ""
        merge_subtests = self.getMergeSubtests(test)
        if err:
            if hide_errors_message:
                output += hide_errors_message
            else:
                if output:
                    # Create a double newline if output is not empty
                    if output.endswith('\n'):
                        output += '\n'
                    else:
                        output += '\n\n'
                output += "{0}{1}\n".format(self.failure_prefix, err[1])
        result = {
            "name": self.getDescription(test),
        }
        if score is not None or weight is not None:
            if weight is None:
                weight = 0.0
            if score is None:
                score = 0.0 if failed else weight
            result["score"] = score
            result["max_score"] = weight
             # Also mark failure if points are lost
            failed |= score < weight

        result["status"] = "failed" if failed else "passed"

        if tags:
            result["tags"] = tags
        if output:
            result["output"] = output
        if visibility:
            result["visibility"] = visibility
        if number:
            result["number"] = number
        if merge_subtests:
            result["merge_subtests"] = merge_subtests
        return result

    def buildLeaderboardEntry(self, test):
        name, sort_order, value = self.getLeaderboardData(test)
        return {
            "name": name,
            "value": value,
            "order": sort_order,
        }

    def processResult(self, test, err=None):
        if self.getLeaderboardData(test)[0]:
            self.leaderboard.append(self.buildLeaderboardEntry(test))
        else:
            self.results.append(self.buildResult(test, err))

    def addSuccess(self, test):
        super(JSONTestResult, self).addSuccess(test)
        self.processResult(test)

    def addError(self, test, err):
        super(JSONTestResult, self).addError(test, err)
        # Prevent output from being printed to stdout on failure
        self._mirrorOutput = False
        self.processResult(test, err)

    def addFailure(self, test, err):
        super(JSONTestResult, self).addFailure(test, err)
        self._mirrorOutput = False
        self.processResult(test, err)

    def addSubTest(self, test, subtest, outcome):
        if outcome == None:
            pass
        else:
            if self.getMergeSubtests(test):
                super(JSONTestResult, self).addFailure(subtest, outcome)
                self._mirrorOutput = False
                self.processResult(test, outcome)
            else:
                super(JSONTestResult, self).addFailure(subtest, outcome)
                self._mirrorOutput = False
                self.processResult(subtest, outcome)


class JSONTestRunner(object):
    """A test runner class that displays results in JSON form.
    """
    resultclass = JSONTestResult

    def __init__(self, stream=sys.stdout, descriptions=True, verbosity=1,
                 failfast=False, buffer=True, visibility=None,
                 stdout_visibility=None, post_processor=None,
                 failure_prefix="Test Failed: "):
        """
        Set buffer to True to include test output in JSON


        post_processor: if supplied, will be called with the final JSON
        data before it is written, allowing the caller to overwrite the
        test results (e.g. add a late penalty) by editing the results
        dict in the first argument.

        failure_prefix: prepended to the output of each test's json
        """
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.post_processor = post_processor
        self.json_data = {
            "tests": [],
            "leaderboard": [],
        }
        if visibility:
            self.json_data["visibility"] = visibility
        if stdout_visibility:
            self.json_data["stdout_visibility"] = stdout_visibility
        self.failure_prefix = failure_prefix

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity,
                                self.json_data["tests"], self.json_data["leaderboard"],
                                self.failure_prefix)
    
    def _checkMergeSubtests(self, list_of_dicts, key):
        "Check if subtests should be merged."
        for dict in list_of_dicts:
            if key in dict:
                return True
        return False

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        startTime = time.time()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            test(result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()
        stopTime = time.time()
        timeTaken = stopTime - startTime

        self.json_data["execution_time"] = format(timeTaken, "0.2f")

        total_score = 0
        for test in self.json_data["tests"]:
            total_score += test.get("score", 0.0)
        self.json_data["score"] = total_score

        if self.post_processor is not None:
            self.post_processor(self.json_data)

        if self._checkMergeSubtests(self.json_data["tests"], "merge_subtests"):

            try:
                if len(self.json_data["tests"]) > 1:

                    i = 0
                    while i < len(self.json_data["tests"]):
                        
                        if (self.json_data["tests"][i]["name"] == self.json_data["tests"][i+1]["name"]
                            and self.json_data["tests"][i]["merge_subtests"] == 'True'):
                            self.json_data["tests"][i]["output"] += self.json_data["tests"][i+1]["output"]
                            del self.json_data["tests"][i+1]

                        else:
                            i += 1
                            if i + 1 >= len(self.json_data["tests"]):
                                break

            except KeyError:
                pass

        json.dump(self.json_data, self.stream, indent=4)
        self.stream.write('\n')

        return result
