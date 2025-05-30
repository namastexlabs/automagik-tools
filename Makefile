# Makefile for automagik-tools development

.PHONY: help install test test-unit test-working test-mcp test-integration test-all test-fast test-coverage lint format clean build publish-test publish check-dist

# Default target
help:
	@echo "AutoMagik Tools Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install the package in development mode"
	@echo ""
	@echo "Testing (using pytest directly):"
	@echo "  test        Run all tests"
	@echo "  test-working Run working/reliable tests only (recommended for development)"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-mcp    Run MCP protocol tests"
	@echo "  test-integration  Run integration tests"
	@echo "  test-fast   Run fast tests (skip slow ones)"
	@echo "  test-coverage     Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint        Run linting (ruff + black check)"
	@echo "  format      Format code (black + ruff fix)"
	@echo ""
	@echo "Build & Publish:"
	@echo "  build       Build the package"
	@echo "  check-dist  Check built package quality"
	@echo "  publish-test Upload to TestPyPI (recommended first)"
	@echo "  publish     Upload to PyPI (production)"
	@echo "  clean       Clean build artifacts"
	@echo ""
	@echo "Direct pytest examples:"
	@echo "  pytest tests/test_unit_fast.py tests/test_cli_simple.py  # Run working tests"
	@echo "  pytest tests/test_unit_fast.py         # Run fast unit tests"
	@echo "  pytest tests/test_cli_simple.py        # Run simple CLI tests"
	@echo "  pytest tests/test_unit_fast.py::TestEvolutionAPITool::test_tool_creation  # Run specific test"
	@echo "  pytest -k 'test_list'                  # Run tests matching pattern"
	@echo "  pytest --cov=automagik_tools           # Run with coverage"

# Ensure .venv is activated for all commands
SHELL := /bin/bash
ACTIVATE := source .venv/bin/activate &&

# Load environment variables from .env file
include .env
export

# Setup
install:
	@echo "Installing automagik-tools in development mode..."
	$(ACTIVATE) uv pip install -e ".[dev]"

# Testing
test:
	@echo "Running all tests..."
	$(ACTIVATE) pytest tests/

test-working:
	@echo "Running working/reliable tests (recommended for development)..."
	$(ACTIVATE) pytest tests/test_unit_fast.py tests/test_cli_simple.py -v

test-unit:
	@echo "Running unit tests..."
	$(ACTIVATE) pytest tests/test_unit_fast.py tests/tools/ -v

test-mcp:
	@echo "Running MCP protocol tests..."
	$(ACTIVATE) pytest tests/test_mcp_protocol.py -v

test-integration:
	@echo "Running integration tests..."
	$(ACTIVATE) pytest tests/test_integration.py -v

test-fast:
	@echo "Running fast tests (skip slow ones)..."
	$(ACTIVATE) pytest tests/ -m "not slow" -v

test-coverage:
	@echo "Running tests with coverage..."
	$(ACTIVATE) pytest tests/ --cov=automagik_tools --cov-report=html --cov-report=term-missing

# Code quality
lint:
	@echo "Running linting checks..."
	$(ACTIVATE) black --check automagik_tools tests
	$(ACTIVATE) ruff check automagik_tools tests

format:
	@echo "Formatting code..."
	$(ACTIVATE) black automagik_tools tests
	$(ACTIVATE) ruff check --fix automagik_tools tests

# Build & Publish
build:
	@echo "Building package..."
	$(ACTIVATE) python -m build --no-isolation

check-dist:
	@echo "Checking built package quality..."
	$(ACTIVATE) twine check dist/*

publish-test: build check-dist
	@echo "Publishing to TestPyPI..."
	@echo "Using API key for user: $(PYPI_USERNAME)"
	$(ACTIVATE) TWINE_USERNAME="__token__" TWINE_PASSWORD="$(PYPI_API_KEY)" twine upload --repository testpypi dist/*

publish: build check-dist
	@echo "Publishing to PyPI..."
	@echo "Using API key for user: $(PYPI_USERNAME)"
	read -p "Are you sure you want to publish to PyPI? (y/N): " confirm && [ "$$confirm" = "y" ]
	$(ACTIVATE) TWINE_USERNAME="__token__" TWINE_PASSWORD="$(PYPI_API_KEY)" twine upload dist/*

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true 