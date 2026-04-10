# Contributing to GivLocal

## Prerequisites

- Python 3.11+
- A GivEnergy inverter (optional — most tests can run without one)

## Dev Setup

```bash
git clone https://github.com/your-org/GivLocal.git
cd GivLocal
python -m venv .venv
source .venv/bin/activate

# Install the modbus library from git
pip install 'givenergy-modbus-async @ git+https://github.com/abedegno/givenergy-modbus-async.git@dev'

# Install the project with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Linting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Pull Request Guidelines

- For large changes, open an issue first to discuss the approach before writing code.
- Include tests for new functionality or bug fixes.
- Ensure all CI checks pass before requesting review.
- Keep PRs focused — one feature or fix per PR makes review easier.
