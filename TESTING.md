Running tests (local and CI)
=================================

This project includes unit tests for MCP tools. The easiest and safest way to run tests locally on Windows is to create a virtual environment and install dev dependencies.

Local (Windows PowerShell)
---------------------------

1. From the repository root run the helper script (recommended):

```powershell
.\scripts\run_tests_windows.ps1
```

2. Or manually create and activate a venv and run tests:

```powershell
# Create and activate venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Upgrade pip and install dev deps
python -m pip install --upgrade pip
python -m pip install -e .[dev]

# Run tests (single file)
python -m pytest tests/tools/test_evolution_api.py -v
```

CI
--

A GitHub Actions workflow is included at `.github/workflows/ci.yml` that installs the project with dev extras and runs the new Evolution API tests. Push a branch or open a PR to trigger CI.

Troubleshooting
---------------
- If Python is provided by MSYS2/WSL and prevents pip operations, create and use a virtual environment as above.
- If tests fail, copy/paste the pytest output and open an issue or ping the maintainer.