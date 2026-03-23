# StreetRace Manager Submission

## Folder Structure

- `whitebox/`: Contains white-box testing code, diagrams, test suite, and the specific report.
- `integration/`: Contains integration testing code, integration call graph diagram, test suite, and report.
- `blackbox/`: Contains black-box testing suite and the report.

## How To Run Code

Run StreetRace Manager CLI from this root directory (`2024113020`):

```bash
PYTHONPATH=integration/code python3 -m streetrace_manager --help
```

## How To Run Tests

Make sure you are in the root directory and you have `pytest` installed. Run the test suites using the following commands:

### 1. Integration Tests
```bash
PYTHONPATH=integration/code python3 -m pytest integration/tests/test_streetrace_integration.py -v
```

### 2. White-box Tests
```bash
PYTHONPATH=whitebox/code python3 -m pytest whitebox/tests/test_monopoly_testing.py -v
```

### 3. Black-box Tests
```bash
python3 -m pytest blackbox/tests -v
```
