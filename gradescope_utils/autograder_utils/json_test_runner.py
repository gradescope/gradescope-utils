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
    def __init__(self, stream, descriptions, verbosity, buffer, results, leaderboard):
        super(JSONTestResult, self).__init__(stream, descriptions, verbosity, buffer)
        self.descriptions = descriptions
        self.results = results
        self.leaderboard = leaderboard

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return doc_first_line
        else:
            return str(test)

    def getTags(self, test):
        return getattr(getattr(test, test._testMethodName), '__tags__', None)

    def getWeight(self, test):
        return getattr(getattr(test, test._testMethodName), '__weight__', 0.0)

    def getScore(self, test):
        return getattr(getattr(test, test._testMethodName), '__score__', None)

    def getVisibility(self, test):
        return getattr(getattr(test, test._testMethodName), '__visibility__', None)

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
        passed = (err == None)

        weight = self.getWeight(test)
        tags = self.getTags(test)
        visibility = self.getVisibility(test)
        score = self.getScore(test)
        if score is None:
            score = weight if passed else 0.0

        output = self.getOutput()
        if err:
            output += "Test Failed: {0}\n".format(err[1])
        result = {
            "name": self.getDescription(test),
            "score": score,
            "max_score": weight,
        }
        if tags:
            result["tags"] = tags
        if output and len(output) > 0:
            result["output"] = output
        if visibility:
            result["visibility"] = visibility
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


class JSONTestRunner(object):
    """A test runner class that displays results in JSON form.
    """
    resultclass = JSONTestResult

    def __init__(self, stream=sys.stdout, descriptions=True, verbosity=1,
                 failfast=False, buffer=True, visibility=None,
                 stdout_visibility=None):
        """
        Set buffer to True to include test output in JSON
        """
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.json_data = {}
        self.json_data["tests"] = []
        self.json_data["leaderboard"] = []
        if visibility:
            self.json_data["visibility"] = visibility
        if stdout_visibility:
            self.json_data["stdout_visibility"] = stdout_visibility

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity, self.buffer,
                                self.json_data["tests"], self.json_data["leaderboard"])

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
            total_score += test["score"]
        self.json_data["score"] = total_score

        json.dump(self.json_data, self.stream, indent=4)
        self.stream.write('\n')
        return result
