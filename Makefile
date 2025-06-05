# ===========================================
# 🛠️ Automagik Tools - Streamlined Makefile
# ===========================================

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
FONT_RED := $(shell tput setaf 1)
FONT_GREEN := $(shell tput setaf 2)
FONT_YELLOW := $(shell tput setaf 3)
FONT_BLUE := $(shell tput setaf 4)
FONT_PURPLE := $(shell tput setaf 5)
FONT_CYAN := $(shell tput setaf 6)
FONT_GRAY := $(shell tput setaf 7)
FONT_BLACK := $(shell tput setaf 8)
FONT_BOLD := $(shell tput bold)
FONT_RESET := $(shell tput sgr0)
CHECKMARK := ✅
WARNING := ⚠️
ERROR := ❌
ROCKET := 🚀
TOOLS := 🛠️
INFO := ℹ️
SPARKLES := ✨

# ===========================================
# 📁 Paths & Configuration
# ===========================================
PROJECT_ROOT := $(shell pwd)
PYTHON := python3
UV := uv

# Load environment variables from .env file if it exists
-include .env
export

# Default values
HOST ?= 127.0.0.1
PORT ?= 8000

# ===========================================
# 🛠️ Utility Functions
# ===========================================
define print_status
	@echo -e "$(FONT_PURPLE)$(TOOLS) $(1)$(FONT_RESET)"
endef

define print_success
	@echo -e "$(FONT_GREEN)$(CHECKMARK) $(1)$(FONT_RESET)"
endef

define print_warning
	@echo -e "$(FONT_YELLOW)$(WARNING) $(1)$(FONT_RESET)"
endef

define print_error
	@echo -e "$(FONT_RED)$(ERROR) $(1)$(FONT_RESET)"
endef

define print_info
	@echo -e "$(FONT_CYAN)$(INFO) $(1)$(FONT_RESET)"
endef

define check_uv
	@if ! command -v uv >/dev/null 2>&1; then \
		$(call print_error,uv not found); \
		echo -e "$(FONT_YELLOW)💡 Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh$(FONT_RESET)"; \
		exit 1; \
	fi
endef

define check_env_file
	@if [ ! -f ".env" ]; then \
		$(call print_warning,.env file not found); \
		echo -e "$(FONT_CYAN)Creating .env from example...$(FONT_RESET)"; \
		cp .env.example .env; \
		$(call print_success,.env created from example); \
		echo -e "$(FONT_YELLOW)💡 Edit .env and add your API keys$(FONT_RESET)"; \
	fi
endef

define show_automagik_logo
	@echo ""
	@echo -e "$(FONT_PURPLE)                                                                                            $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)                                                                                            $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)     -+*         -=@%*@@@@@@*  -#@@@%*  =@@*      -%@#+   -*       +%@@@@*-%@*-@@*  -+@@*   $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)     =@#*  -@@*  -=@%+@@@@@@*-%@@#%*%@@+=@@@*    -+@@#+  -@@*   -#@@%%@@@*-%@+-@@* -@@#*    $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)    -%@@#* -@@*  -=@@* -@%* -@@**   --@@=@@@@*  -+@@@#+ -#@@%* -*@%*-@@@@*-%@+:@@+#@@*      $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)   -#@+%@* -@@*  -=@@* -@%* -@@*-+@#*-%@+@@=@@* +@%#@#+ =@##@* -%@#*-@@@@*-%@+-@@@@@*       $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  -*@#==@@*-@@*  -+@%* -@%* -%@#*   -+@@=@@++@%-@@=*@#=-@@*-@@*:+@@*  -%@*-%@+-@@#*@@**     $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  -@@* -+@%-+@@@@@@@*  -@%*  -#@@@@%@@%+=@@+-=@@@*    -%@*  -@@*-*@@@@%@@*#@@#=%*  -%@@*    $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE) -@@*+  -%@*  -#@%+    -@%+     =#@@*   =@@+          +@%+  -#@#   -*%@@@*@@@@%+     =@@+   $(FONT_RESET)"
	@echo ""
endef

define show_nmstx_logo
	@echo ""
	@echo -e "$(FONT_PURPLE)  :*@@@@*.     :=@@@-%@@@%=          :-@@@%* :*@@@@@@@#-:#@@@@@@@@@@@*-           -#@@@%=   $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@@@#-    :=@@@-%@@@@#=        :-@@@@%--@@@@@%@@@@%-============-.          -@@@@*=    $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@@@@#=   :=@@@-%@@@@@*-      .-@@@@@%-#@@@*  .-%@%+=              :+@@@@*.=@@@@*.     $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@#@@@%*  :=@@@-%@@@@@@*-     -%@@@@@%-#@@@*                        .-@@@@%@@@%+       $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@--@@@@*::=@@@-%@@@%@@@*:   -#@@@@@@%--@@@@@%%#+:     :*@@@*.        -*@@@@@*=        $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@*.-%@@@#:=@@@-%@@@-#@@@*. -*@@@=+@@%* :-@@@@@@@@#-   :*@@@*.        .=@@@@@*.        $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@*. -#@@@#+@@@-%@@@=-#@@@+-+@@@*-+@@%*      .-#@@@*:  :*@@@*.       -*@@@@@@@*-       $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)  :*@@@*.  :=@@@@@@@-%@@@*.-@@@%*@@@*--+@@%*       .-@@@**  :*@@@*.      -@@@@#-#@@@%=      $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)            .-@@@@@@-%@@@*..-@@@@@@*=             .=%@@@*.  :*@@@*.    .-@@@@*. .:==-::   $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)              -#@@@@-%@@@*. .-@@@@#=             -+@@@@*:   :*@@@*.   -+@@@%+               $(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)               :=+++:=+++-                       ::=-:      .-+++-   :=+++=:                $(FONT_RESET)"
	@echo ""
endef

define print_success_with_logo
	@echo -e "$(FONT_GREEN)$(CHECKMARK) $(1)$(FONT_RESET)"
	@$(call show_automagik_logo)
endef

# ===========================================
# 📋 Help System
# ===========================================
.PHONY: help
help: ## 🛠️ Show this help message
	@$(call show_automagik_logo)
	@echo -e "$(FONT_BOLD)$(FONT_PURPLE)🛠️ Automagik Tools$(FONT_RESET) - $(FONT_GRAY)The Premier Repository for MCP Tools$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_YELLOW)🏢 Making MCP tool development automagik$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)📦 GitHub:$(FONT_RESET) https://github.com/namastexlabs/automagik-tools"
	@echo ""
	@echo -e "$(FONT_PURPLE)✨ \"The largest collection of MCP tools, with trivially easy development\"$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_CYAN)$(ROCKET) Quick Start:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)install$(FONT_RESET)         Install development environment"
	@echo -e "  $(FONT_PURPLE)list$(FONT_RESET)            List available tools"
	@echo -e "  $(FONT_PURPLE)serve-evolution$(FONT_RESET) Run Evolution API (Claude Desktop ready)"
	@echo ""
	@echo -e "$(FONT_CYAN)$(TOOLS) Development:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)test$(FONT_RESET)            Run all tests"
	@echo -e "  $(FONT_PURPLE)test-working$(FONT_RESET)    Run stable tests only"
	@echo -e "  $(FONT_PURPLE)test-unit$(FONT_RESET)       Run unit tests"
	@echo -e "  $(FONT_PURPLE)test-mcp$(FONT_RESET)        Run MCP protocol tests"
	@echo -e "  $(FONT_PURPLE)test-coverage$(FONT_RESET)   Run tests with coverage"
	@echo ""
	@echo -e "$(FONT_CYAN)🎨 Code Quality:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)lint$(FONT_RESET)            Check code style"
	@echo -e "  $(FONT_PURPLE)format$(FONT_RESET)          Auto-format code"
	@echo ""
	@echo -e "$(FONT_CYAN)📦 Build & Publish:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)build$(FONT_RESET)           Build package"
	@echo -e "  $(FONT_PURPLE)publish-test$(FONT_RESET)    Upload to TestPyPI"
	@echo -e "  $(FONT_PURPLE)publish$(FONT_RESET)         Upload to PyPI + GitHub release"
	@echo -e "  $(FONT_PURPLE)bump-patch$(FONT_RESET)      Bump patch version (x.x.1)"
	@echo -e "  $(FONT_PURPLE)bump-minor$(FONT_RESET)      Bump minor version (x.1.0)"
	@echo -e "  $(FONT_PURPLE)bump-major$(FONT_RESET)      Bump major version (1.0.0)"
	@echo -e "  $(FONT_PURPLE)clean$(FONT_RESET)           Clean build artifacts"
	@echo ""
	@echo -e "$(FONT_CYAN)$(SPARKLES) Tool Commands:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)info TOOL=name$(FONT_RESET)  Show tool information"
	@echo -e "  $(FONT_PURPLE)run TOOL=name$(FONT_RESET)   Run tool standalone"
	@echo -e "  $(FONT_PURPLE)serve-all$(FONT_RESET)       Serve all tools"
	@echo -e "  $(FONT_PURPLE)tool URL=url$(FONT_RESET)    Create tool from OpenAPI spec"
	@echo ""
	@echo -e "$(FONT_GRAY)Examples:$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make info TOOL=evolution-api$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make test-unit$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)uvx automagik-tools serve --tool evolution-api$(FONT_RESET)"
	@echo ""

# ===========================================
# 🚀 Installation & Setup
# ===========================================
.PHONY: install
install: ## $(ROCKET) Install development environment with uv
	$(call print_status,Installing automagik-tools development environment...)
	@$(call check_uv)
	@$(call check_env_file)
	@$(UV) sync --all-extras
	$(call print_success_with_logo,Development environment ready!)
	@echo -e "$(FONT_CYAN)💡 Try: make list$(FONT_RESET)"

# ===========================================
# 🧪 Testing
# ===========================================
.PHONY: test test-working test-unit test-mcp test-coverage
test: ## 🧪 Run all tests
	$(call print_status,Running all tests...)
	@$(UV) run pytest tests/ -v

test-working: ## ✅ Run stable/working tests only
	$(call print_status,Running stable tests...)
	@$(UV) run pytest tests/test_unit_fast.py tests/test_cli_simple.py -v

test-unit: ## 🔬 Run unit tests
	$(call print_status,Running unit tests...)
	@$(UV) run pytest tests/test_unit*.py -v

test-mcp: ## 🔌 Run MCP protocol compliance tests
	$(call print_status,Running MCP protocol tests...)
	@$(UV) run pytest tests/test_mcp_protocol.py -v

test-coverage: ## 📊 Run tests with coverage report
	$(call print_status,Running tests with coverage...)
	@$(UV) run pytest tests/ --cov=automagik_tools --cov-report=html --cov-report=term

# ===========================================
# 🎨 Code Quality
# ===========================================
.PHONY: lint format
lint: ## 🔍 Check code style (black + ruff)
	$(call print_status,Checking code style...)
	@$(UV) run black --check automagik_tools tests
	@$(UV) run ruff check automagik_tools tests
	$(call print_success,Code style check complete!)

format: ## 🎨 Auto-format code
	$(call print_status,Formatting code...)
	@$(UV) run black automagik_tools tests
	@$(UV) run ruff check --fix automagik_tools tests
	$(call print_success,Code formatted!)

# ===========================================
# 📦 Build & Publish
# ===========================================
.PHONY: build publish-test publish check-dist check-release
build: clean ## 📦 Build package
	$(call print_status,Building package...)
	@$(UV) build
	$(call print_success,Package built!)

check-dist: ## 🔍 Check package quality
	$(call print_status,Checking package quality...)
	@$(UV) run twine check dist/*

check-release: ## 🔍 Check if ready for release (clean working directory)
	$(call print_status,Checking release readiness...)
	@# Check for uncommitted changes
	@if [ -n "$$(git status --porcelain)" ]; then \
		$(call print_error,Uncommitted changes detected!); \
		echo -e "$(FONT_YELLOW)Please commit or stash your changes before publishing.$(FONT_RESET)"; \
		echo -e "$(FONT_CYAN)Run: git status$(FONT_RESET)"; \
		exit 1; \
	fi
	@# Check if on main branch
	@CURRENT_BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$CURRENT_BRANCH" != "main" ]; then \
		$(call print_warning,Not on main branch (current: $$CURRENT_BRANCH)); \
		echo -e "$(FONT_YELLOW)It's recommended to publish from the main branch.$(FONT_RESET)"; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			exit 1; \
		fi; \
	fi
	@# Check if main branch is up to date with origin
	@git fetch origin main --quiet; \
	@if [ "$$(git rev-parse HEAD)" != "$$(git rev-parse origin/main)" ]; then \
		$(call print_warning,Local main branch differs from origin/main); \
		echo -e "$(FONT_YELLOW)Consider pulling latest changes or pushing your commits.$(FONT_RESET)"; \
		echo -e "$(FONT_CYAN)Run: git pull origin main$(FONT_RESET)"; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			exit 1; \
		fi; \
	fi
	$(call print_success,Ready for release!)

publish-test: build check-dist ## 🧪 Upload to TestPyPI
	$(call print_status,Publishing to TestPyPI...)
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		$(call print_error,PYPI_TOKEN not set); \
		exit 1; \
	fi
	@$(UV) run twine upload --repository testpypi dist/* -u __token__ -p "$(PYPI_TOKEN)"
	$(call print_success,Published to TestPyPI!)

publish: check-release build check-dist ## $(ROCKET) Upload to PyPI and create GitHub release
	$(call print_status,Publishing to PyPI and GitHub...)
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		echo -e "$(FONT_RED)$(ERROR) PYPI_TOKEN environment variable not set$(FONT_RESET)"; \
		exit 1; \
	fi
	@# Get version from pyproject.toml
	@VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	echo -e "$(FONT_CYAN)$(INFO) Publishing version: v$$VERSION$(FONT_RESET)"; \
	\
	# Upload to PyPI
	$(UV) run twine upload dist/* -u __token__ -p "$(PYPI_TOKEN)"; \
	\
	# Create git tag if it doesn't exist
	if ! git tag | grep -q "^v$$VERSION$$"; then \
		echo -e "$(FONT_CYAN)$(INFO) Creating git tag v$$VERSION$(FONT_RESET)"; \
		git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	fi; \
	\
	# Push tag to GitHub
	echo -e "$(FONT_CYAN)$(INFO) Pushing tag to GitHub$(FONT_RESET)"; \
	git push origin "v$$VERSION"; \
	\
	# Create GitHub release using gh CLI if available
	if command -v gh >/dev/null 2>&1; then \
		echo -e "$(FONT_CYAN)$(INFO) Creating GitHub release$(FONT_RESET)"; \
		gh release create "v$$VERSION" \
			--title "v$$VERSION" \
			--notes "Release v$$VERSION - See CHANGELOG for details" \
			dist/* || echo -e "$(FONT_YELLOW)$(WARNING) GitHub release creation failed (may already exist)$(FONT_RESET)"; \
	else \
		echo -e "$(FONT_YELLOW)$(WARNING) GitHub CLI (gh) not found - skipping release creation$(FONT_RESET)"; \
		echo -e "$(FONT_CYAN)$(INFO) Install with: brew install gh$(FONT_RESET)"; \
	fi
	$(call print_success,Published to PyPI and GitHub!)

# ===========================================
# 📈 Version Management
# ===========================================
.PHONY: bump-patch bump-minor bump-major
bump-patch: ## 📈 Bump patch version (0.1.0 -> 0.1.1)
	$(call print_status,Bumping patch version...)
	@CURRENT_VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	NEW_VERSION=$$(echo $$CURRENT_VERSION | awk -F. '{$$NF = $$NF + 1;} 1' | sed 's/ /./g'); \
	sed -i "s/version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	echo -e "$(FONT_GREEN)✅ Version bumped from $$CURRENT_VERSION to $$NEW_VERSION$(FONT_RESET)"

bump-minor: ## 📈 Bump minor version (0.1.0 -> 0.2.0)
	$(call print_status,Bumping minor version...)
	@CURRENT_VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	NEW_VERSION=$$(echo $$CURRENT_VERSION | awk -F. '{$$2 = $$2 + 1; $$3 = 0;} 1' | sed 's/ /./g'); \
	sed -i "s/version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	echo -e "$(FONT_GREEN)✅ Version bumped from $$CURRENT_VERSION to $$NEW_VERSION$(FONT_RESET)"

bump-major: ## 📈 Bump major version (0.1.0 -> 1.0.0)
	$(call print_status,Bumping major version...)
	@CURRENT_VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	NEW_VERSION=$$(echo $$CURRENT_VERSION | awk -F. '{$$1 = $$1 + 1; $$2 = 0; $$3 = 0;} 1' | sed 's/ /./g'); \
	sed -i "s/version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	echo -e "$(FONT_GREEN)✅ Version bumped from $$CURRENT_VERSION to $$NEW_VERSION$(FONT_RESET)"

# ===========================================
# 🧹 Maintenance
# ===========================================
.PHONY: clean
clean: ## 🧹 Clean build artifacts and cache
	$(call print_status,Cleaning build artifacts...)
	@$(UV) cache clean
	@rm -rf build dist *.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf coverage.xml
	$(call print_success,Cleanup complete!)

# ===========================================
# $(SPARKLES) Tool Commands
# ===========================================
.PHONY: list info run serve-evolution serve-all
list: ## 📋 List available tools
	@$(UV) run automagik-tools list

info: ## $(INFO) Show tool information (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make info TOOL=<tool-name>); \
		echo -e "$(FONT_GRAY)Example: make info TOOL=evolution-api$(FONT_RESET)"; \
		exit 1; \
	fi
	@$(UV) run automagik-tools info $(TOOL)

run: ## $(ROCKET) Run tool standalone (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make run TOOL=<tool-name>); \
		echo -e "$(FONT_GRAY)Example: make run TOOL=evolution-api$(FONT_RESET)"; \
		exit 1; \
	fi
	@$(UV) run automagik-tools run $(TOOL)

serve-evolution: ## 🚀 Run Evolution API (Claude Desktop ready)
	$(call print_status,Starting Evolution API in stdio mode...)
	@$(call check_env_file)
	@if [ -n "$(EVOLUTION_API_BASE_URL)" ]; then \
		echo -e "$(FONT_CYAN)Using EVOLUTION_API_BASE_URL: $(EVOLUTION_API_BASE_URL)$(FONT_RESET)"; \
	fi
	@if [ -n "$(EVOLUTION_API_KEY)" ]; then \
		echo -e "$(FONT_CYAN)Using EVOLUTION_API_KEY: ***$(FONT_RESET)"; \
	fi
	@uvx automagik-tools serve --tool evolution-api --transport stdio

serve-all: ## 🌐 Serve all tools on single server
	$(call print_status,Starting multi-tool server on $(HOST):$(PORT)...)
	@$(UV) run automagik-tools serve-all --host $(HOST) --port $(PORT)

# ===========================================
# 🔧 Tool Creation
# ===========================================
.PHONY: tool
tool: ## 🔧 Create new tool from OpenAPI spec (use URL=<openapi-url> NAME=<tool-name>)
	@if [ -z "$(URL)" ]; then \
		$(call print_error,Usage: make tool URL=<openapi-json-url> [NAME=<tool-name>]); \
		echo -e "$(FONT_GRAY)Example: make tool URL=https://api.example.com/openapi.json NAME=\"My API\"$(FONT_RESET)"; \
		exit 1; \
	fi
	$(call print_status,Creating tool from OpenAPI specification...)
	@if [ -n "$(NAME)" ]; then \
		$(UV) run python scripts/create_tool_from_openapi_v2.py --url "$(URL)" --name "$(NAME)" --force; \
	else \
		$(UV) run python scripts/create_tool_from_openapi_v2.py --url "$(URL)" --force; \
	fi
	$(call print_success,Tool created successfully!)

# ===========================================
# 🚀 FastMCP Native Commands
# ===========================================
.PHONY: fastmcp-hub fastmcp-evolution fastmcp-hello fastmcp-dev
fastmcp-hub: ## 🌐 Run hub server with FastMCP CLI
	$(call print_status,Starting hub server with FastMCP...)
	@$(UV) run fastmcp run automagik_tools.servers.hub:hub

fastmcp-evolution: ## 📱 Run Evolution API with FastMCP CLI
	$(call print_status,Starting Evolution API with FastMCP...)
	@$(UV) run fastmcp run automagik_tools.servers.evolution_api:mcp

fastmcp-hello: ## 👋 Run Example Hello with FastMCP CLI
	$(call print_status,Starting Example Hello with FastMCP...)
	@$(UV) run fastmcp run automagik_tools.servers.example_hello:mcp

fastmcp-dev: ## 🔧 Run hub with FastMCP Inspector
	$(call print_status,Starting hub with MCP Inspector...)
	@$(UV) run fastmcp dev automagik_tools.servers.hub:hub

# ===========================================
# 🧪 Advanced Testing
# ===========================================
.PHONY: test-fast test-integration test-nodebug
test-fast: ## ⚡ Run fast tests only
	$(call print_status,Running fast tests...)
	@$(UV) run pytest tests/ -m "not slow" -v

test-integration: ## 🔗 Run integration tests
	$(call print_status,Running integration tests...)
	@$(UV) run pytest tests/test_integration.py -v

test-nodebug: ## 🤫 Run tests without debug logging
	$(call print_status,Running tests without debug...)
	@LOG_LEVEL=INFO $(UV) run pytest tests/ -v

# ===========================================
# 🎨 Additional Commands
# ===========================================
.PHONY: watch type-check
watch: ## 👀 Watch for changes and restart
	$(call print_status,Watching for changes...)
	@$(UV) run watchmedo auto-restart -d automagik_tools -p "*.py" -- make serve-all

type-check: ## 🔍 Run type checking with mypy
	$(call print_status,Running type checks...)
	@$(UV) run mypy automagik_tools

# ===========================================
# 🛠️ Direct pytest examples
# ===========================================
.PHONY: test-specific test-pattern
test-specific: ## 🎯 Run specific test file
	@echo -e "$(FONT_GRAY)Examples:$(FONT_RESET)"
	@echo -e "$(FONT_GRAY)  pytest tests/test_unit_fast.py::TestEvolutionAPITool::test_tool_creation$(FONT_RESET)"
	@echo -e "$(FONT_GRAY)  pytest tests/test_cli_simple.py$(FONT_RESET)"

test-pattern: ## 🔍 Run tests matching pattern
	@echo -e "$(FONT_GRAY)Examples:$(FONT_RESET)"
	@echo -e "$(FONT_GRAY)  pytest -k 'test_list'$(FONT_RESET)"
	@echo -e "$(FONT_GRAY)  pytest -k 'evolution'$(FONT_RESET)"

# ===========================================
# 📚 Documentation
# ===========================================
.PHONY: docs
docs: ## 📚 Serve documentation locally
	$(call print_status,Starting documentation server...)
	@echo -e "$(FONT_YELLOW)📚 Documentation server not yet implemented$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 View README.md for documentation$(FONT_RESET)"

# Ensure default goal shows help
.DEFAULT_GOAL := help