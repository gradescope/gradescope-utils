import unittest
from gradescope_utils.autograder_utils.json_test_runner import JSONTestRunner

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
#        raise AssertionError("This shouldnt crash the entire platform")
        pass

    def test1(self):
        pass


if __name__ == "__main__":
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
    resultsPath = "./results.json"

    with open(resultsPath, 'w') as w:
        runner = JSONTestRunner(w)
        runner.run(tests)


