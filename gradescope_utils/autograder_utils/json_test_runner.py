"""Running tests"""
from __future__ import print_function

import os
import sys
import time
import traceback
import json

from unittest import result
from unittest.signals import registerResult


class JSONTestResult(result.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by JSONTestRunner.
    """
    def __init__(self, stream, descriptions, verbosity, results, leaderboard):
        super(JSONTestResult, self).__init__(stream, descriptions, verbosity)
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

    def getNumber(self, test):
        return getattr(getattr(test, test._testMethodName), '__number__', None)

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
        number = self.getNumber(test)
        visibility = self.getVisibility(test)
        score = self.getScore(test)
        if score is None:
            score = weight if passed else 0.0

        output = self.getOutput()
        if err:
            # When the error is due to an exception in the user's code,
            # we provide a stack backtrace so the user is not left wondering
            # why their code failed.
            if not isinstance(err[0], AssertionError):
                # Get formatted traceback and create a string describing the
                # problem in the user code
                stackbt = traceback.extract_tb(err[2])
                # Number of frames of backtrace, can be changed to provide
                # more detail, but we don't want to go all the way to the
                # test case.
                Nframes = 1
                # gather frame information and create details message
                msgs = []
                for frame in range(-Nframes, 0):
                    # format as:  filename:function line N: program text
                    msgs.append("%s:%s line %d: %s"%(
                        os.path.basename(stackbt[frame].filename),
                        stackbt[frame].name, stackbt[frame].lineno,
                        stackbt[frame].line))
                details = "\n"+"\n".join(msgs)
            else:
                details = ""
            # Report error and method/line on which it occurred
            output += "Test Failed: {}{}\n".format(err[1], details)

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
        if number:
            result["number"] = number
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
                 stdout_visibility=None, post_processor=None):
        """
        Set buffer to True to include test output in JSON


        post_processor: if supplied, will be called with the final JSON
        data before it is written, allowing the caller to overwrite the
        test results (e.g. add a late penalty) by editing the results
        dict in the first argument.
        """
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.post_processor = post_processor
        self.json_data = {}
        self.json_data["tests"] = []
        self.json_data["leaderboard"] = []
        if visibility:
            self.json_data["visibility"] = visibility
        if stdout_visibility:
            self.json_data["stdout_visibility"] = stdout_visibility

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity,
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

        if self.post_processor is not None:
            self.post_processor(self.json_data)

        json.dump(self.json_data, self.stream, indent=4)
        self.stream.write('\n')
        return result
