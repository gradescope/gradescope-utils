# autograder_utils

This package provides some helper classes which assist in developing autograders
for the Gradescope autograder platform. These utilities work together to make it
easy to use Python's built in `unittest` module for creating autograders that
work on Gradescope.

## decorators

Decorators are provided for annotating test cases.

### @weight

The `@weight` decorator allows setting the point value of a test case. This
information is used by the JSONTestRunner in producing its output. This is
required for any tests which award points.

Example:
```
@weight(5.0)
def test_functionality():
    ...
```

### @tags

The `@tags` decorator allows setting tags on a test case. This is optional, but
may be used in the future to enable analytics on the concepts being tested in
programming assignments.

Example:
```
@tags("conditionals", "recursion")
def test_search():
    ...
```

### @visibility

The `@visibility` decorator allows setting the visibility of a test case.

Example:
```
@visibility("after_due_date")
def test_search():
    ...
```

## unittest utilities

### JSONTestRunner

This utility class is a custom unittest test runner which produces JSON output
in the format that Gradescope's infrastructure expects. It works with test cases
annotated with the `@weight` annotation to determine the point value of each
test case.

Example:
```
suite = unittest.defaultTestLoader.discover('tests')
with open('results.json', 'w') as f:
    JSONTestRunner(stream=f, verbosity=2, buffer=True).run(suite)
```

### JSONTestResult

This class is used by JSONTestRunner to format output in JSON.

Example output:

```
{
    "output": "Printing inside a test case\n",
    "score": 3,
    "max_score": 3,
    "name": "Test parsing a simple expression",
    "tags": [
        "parsing",
        "lexing"
    ]
}
```

### GradescopeDjangoRunner
This allows for an integration between Django testing, which utilizes unittest and 
Gradescope's JSONTestRunner to obtain the JSON output of the Django test cases. 
To enable this, complete the following steps:  

First, in your settings.py, insert the lines:
```python
TEST_RUNNER = 'gradescope_utils.autograder_utils.gradescope_django_runner.GradescopeDjangoRunner'

GRADESCOPE_PARAMETERS = {
    'stream': sys.stdout,
    'descriptions': True,
    'verbosity': 1,
    'failfast': False,
    'buffer': True,
    'visibility': "visible",
    'stdout_visibility': None,
    'post_processor': None,
    'failure_prefix': "Test Failed: "
}
```
The `gradescope_parameters` is used to set arguments for the JSONTestRunner.

Then, within your `run_autograder`, run the following command:
```
python3 manage.py test -v 0 > /autograder/results/results.json
```
