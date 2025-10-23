<#
PowerShell helper to create a virtual environment and run the project's tests on Windows.

Usage (from repo root):
  .\scripts\run_tests_windows.ps1

This script will:
 - create a .venv directory if missing
 - activate the venv for the current session
 - upgrade pip
 - install dev dependencies (editable mode)
 - run pytest for the new evolution_api tests

Note: Run from an elevated prompt only if necessary. If your Python is managed by MSYS2, create and use a venv to avoid system package manager restrictions.
#>

Set-StrictMode -Version Latest

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "python not found in PATH. Install Python 3.10+ and ensure 'python' is on PATH."
    exit 1
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvDir = Join-Path $repoRoot ".venv"

if (-not (Test-Path $venvDir)) {
  Write-Host "Creating virtual environment at $venvDir..."
  python -m venv $venvDir
}

# Activate the venv for this session (repo-root .venv)
$activateScriptOptions = @(
  Join-Path $venvDir "Scripts\Activate.ps1",
  Join-Path $venvDir "bin\Activate.ps1"
)

$activateScript = $activateScriptOptions | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $activateScript) {
  Write-Error "Activation script not found in .venv (looked in Scripts and bin). Create a venv manually and activate it."
  exit 1
}

Write-Host "Activating venv ($activateScript)..."
& $activateScript

Write-Host "Upgrading pip and installing dev dependencies..."
python -m pip install --upgrade pip
python -m pip install -e .[dev]

Write-Host "Running tests for Evolution API tool..."
python -m pytest tests/tools/test_evolution_api.py -v
