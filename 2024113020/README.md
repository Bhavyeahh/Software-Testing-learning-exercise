# StreetRace Manager / Assignments

## How to run the code

Run StreetRace Manager CLI (Integration) from the root directory:
```bash
PYTHONPATH=integration/code python3 -m streetrace_manager --help
```

## How to run the tests

Run the following commands from the root directory of the repository:

**1. White-box Tests (Monopoly)**
```bash
PYTHONPATH=whitebox/code/moneypoly/moneypoly python3 -m pytest whitebox/tests/ -v
```

**2. Integration Tests (StreetRace Manager)**
```bash
PYTHONPATH=integration/code python3 -m pytest integration/tests/ -v
```

**3. Black-box Tests (QuickCart)**

First, load and start the QuickCart API Docker server (assuming the `.tar` is in the parent directory):
```bash
docker load -i ../quickcart_image.tar
docker run -d -p 8080:8080 quickcart
```

Then, run the tests:
```bash
python3 -m pytest blackbox/tests -v
```

## Git Repository Link
- Add your URL here: `https://github.com/Bhavyeahh/Software-Testing-learning-exercise.git`
