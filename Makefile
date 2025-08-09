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
TOOLS_SYMBOL := 🛠️
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
AUTOMAGIK_TOOLS_HOST ?= 127.0.0.1
AUTOMAGIK_TOOLS_SSE_PORT ?= 8884
AUTOMAGIK_TOOLS_HTTP_PORT ?= 8885

# Simplified aliases for command-line use
HOST ?= $(AUTOMAGIK_TOOLS_HOST)
PORT ?= $(AUTOMAGIK_TOOLS_SSE_PORT)

# ===========================================
# 🛠️ Utility Functions
# ===========================================
define print_status
	@echo -e "$(FONT_PURPLE)$(TOOLS_SYMBOL) $(1)$(FONT_RESET)"
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

define check_prerequisites
	@if ! command -v uv >/dev/null 2>&1 || ! command -v make >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then \
		echo -e "$(FONT_RED)$(ERROR) Missing dependencies detected$(FONT_RESET)"; \
		echo -e "$(FONT_YELLOW)💡 Run the full installer: ./scripts/install.sh$(FONT_RESET)"; \
		exit 1; \
	fi
endef

define ensure_env_file
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo -e "$(FONT_CYAN)$(INFO) .env created from example$(FONT_RESET)"; \
	fi
endef

define show_automagik_logo
	[ -z "$$AUTOMAGIK_QUIET_LOGO" ] && { \
		echo ""; \
		echo -e "$(FONT_PURPLE)                                                                                            $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)                                                                                            $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)     -+*         -=@%*@@@@@@*  -#@@@%*  =@@*      -%@#+   -*       +%@@@@*-%@*-@@*  -+@@*   $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)     =@#*  -@@*  -=@%+@@@@@@*-%@@#%*%@@+=@@@*    -+@@#+  -@@*   -#@@%%@@@*-%@+-@@* -@@#*    $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)    -%@@#* -@@*  -=@@* -@%* -@@**   --@@=@@@@*  -+@@@#+ -#@@%* -*@%*-@@@@*-%@+:@@+#@@*      $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)   -#@+%@* -@@*  -=@@* -@%* -@@*-+@#*-%@+@@=@@* +@%#@#+ =@##@* -%@#*-@@@@*-%@+-@@@@@*       $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)  -*@#==@@*-@@*  -+@%* -@%* -%@#*   -+@@=@@++@%-@@=*@#=-@@*-@@*:+@@*  -%@*-%@+-@@#*@@**     $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)  -@@* -+@%-+@@@@@@@*  -@%*  -#@@@@%@@%+=@@+-=@@@*    -%@*  -@@*-*@@@@%@@*#@@#=%*  -%@@*    $(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE) -@@*+  -%@*  -#@%+    -@%+     =#@@*   =@@+          +@%+  -#@#   -*%@@@*@@@@%+     =@@+   $(FONT_RESET)"; \
		echo ""; \
	} || true
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
	@echo -e "  $(FONT_PURPLE)install-full$(FONT_RESET)    Full system install (recommended for new setups)"
	@echo -e "  $(FONT_PURPLE)install$(FONT_RESET)         Quick install (if dependencies already exist)"
	@echo -e "  $(FONT_PURPLE)list$(FONT_RESET)            List available tools"
	@echo -e "  $(FONT_PURPLE)serve-all$(FONT_RESET)       Serve all tools on single transport (SSE)"
	@echo -e "  $(FONT_PURPLE)serve-dual$(FONT_RESET)      Serve all tools on dual transports (SSE+HTTP)"
	@echo ""
	@echo -e "$(FONT_CYAN)$(TOOLS_SYMBOL) Development:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)test$(FONT_RESET)            Run all tests"
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
	@echo -e "  $(FONT_PURPLE)bump-dev$(FONT_RESET)        Create dev version (0.1.2pre1)"
	@echo -e "  $(FONT_PURPLE)publish-dev$(FONT_RESET)     Publish dev version to PyPI"
	@echo -e "  $(FONT_PURPLE)finalize-version$(FONT_RESET) Remove 'pre' suffix (0.1.2pre3 -> 0.1.2)"
	@echo -e "  $(FONT_PURPLE)publish-test$(FONT_RESET)    Upload current version to TestPyPI"
	@echo -e "  $(FONT_PURPLE)publish$(FONT_RESET)         Upload to PyPI + GitHub release"
	@echo -e "  $(FONT_PURPLE)bump-patch$(FONT_RESET)      Bump patch version (x.x.1)"
	@echo -e "  $(FONT_PURPLE)bump-minor$(FONT_RESET)      Bump minor version (x.1.0)"
	@echo -e "  $(FONT_PURPLE)bump-major$(FONT_RESET)      Bump major version (1.0.0)"
	@echo -e "  $(FONT_PURPLE)clean$(FONT_RESET)           Clean build artifacts"
	@echo ""
	@echo -e "$(FONT_CYAN)🐳 Docker Commands:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)docker-build$(FONT_RESET)    Build all Docker images"
	@echo -e "  $(FONT_PURPLE)docker-build-sse$(FONT_RESET) Build SSE transport image"
	@echo -e "  $(FONT_PURPLE)docker-build-http$(FONT_RESET) Build HTTP transport image"
	@echo -e "  $(FONT_PURPLE)docker-run-sse$(FONT_RESET)  Run SSE server in Docker"
	@echo -e "  $(FONT_PURPLE)docker-run-http$(FONT_RESET) Run HTTP server in Docker"
	@echo -e "  $(FONT_PURPLE)docker-compose$(FONT_RESET)  Run multi-transport setup"
	@echo -e "  $(FONT_PURPLE)docker-deploy$(FONT_RESET)   Deploy to cloud (PROVIDER=railway|aws|gcloud|render)"
	@echo ""
	@echo -e "$(FONT_CYAN)$(SPARKLES) Tool Commands:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)serve TOOL=name$(FONT_RESET)  Serve single tool (with optional TRANSPORT=)"
	@echo -e "  $(FONT_PURPLE)serve-all$(FONT_RESET)       Serve all tools on multi-tool server"
	@echo -e "  $(FONT_PURPLE)dev-server$(FONT_RESET)      Development server with hot-reload"
	@echo -e "  $(FONT_PURPLE)info TOOL=name$(FONT_RESET)  Show tool information"
	@echo -e "  $(FONT_PURPLE)run TOOL=name$(FONT_RESET)   Run tool standalone"
	@echo -e "  $(FONT_PURPLE)tool URL=url$(FONT_RESET)    Create tool from OpenAPI spec"
	@echo -e "  $(FONT_PURPLE)new-tool$(FONT_RESET)        Create new tool interactively"
	@echo -e "  $(FONT_PURPLE)test-tool$(FONT_RESET)       Test specific tool (use TOOL=name)"
	@echo -e "  $(FONT_PURPLE)validate-tool$(FONT_RESET)   Validate tool compliance (TOOL=name)"
	@echo -e "  $(FONT_PURPLE)mcp-config$(FONT_RESET)      Generate MCP config for Cursor/Claude (TOOL=name)"
	@echo ""
	@echo -e "$(FONT_CYAN)🌐 HTTP Development Deployment:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)http-start$(FONT_RESET)      Start HTTP development server (HOST= PORT= TOOLS=)"
	@echo -e "  $(FONT_PURPLE)http-stop$(FONT_RESET)       Stop HTTP development server (PORT=)"
	@echo -e "  $(FONT_PURPLE)http-restart$(FONT_RESET)    Restart HTTP development server"
	@echo -e "  $(FONT_PURPLE)http-status$(FONT_RESET)     Check HTTP server status"
	@echo -e "  $(FONT_PURPLE)http-logs$(FONT_RESET)       Show HTTP server logs"
	@echo -e "  $(FONT_PURPLE)http-dev$(FONT_RESET)        Quick development setup (localhost:8000)"
	@echo -e "  $(FONT_PURPLE)http-network$(FONT_RESET)    Network accessible setup (0.0.0.0:8000)"
	@echo ""
	@echo -e "$(FONT_GRAY)Examples:$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make serve TOOL=evolution-api$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make serve TOOL=automagik-agents TRANSPORT=streamable-http$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make dev-server$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make new-tool$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make test-tool TOOL=evolution-api$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make validate-tool TOOL=automagik-agents$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make mcp-config TOOL=discord-api$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make docker-build-sse$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make docker-run-sse PORT=8000$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make docker-compose$(FONT_RESET)"
	@echo -e "  $(FONT_GRAY)make docker-deploy PROVIDER=aws$(FONT_RESET)"
	@echo ""

# ===========================================
# 🚀 Installation & Setup
# ===========================================
.PHONY: install install-full install-deps
install: ## $(ROCKET) Quick install (assumes dependencies exist)
	$(call print_status,Installing automagik-tools (quick mode)...)
	@$(call check_prerequisites)
	@$(call ensure_env_file)
	@$(UV) sync --all-extras
	$(call print_success_with_logo,Development environment ready!)
	@echo -e "$(FONT_CYAN)💡 Try: make list$(FONT_RESET)"

install-full: ## $(ROCKET) Full system install (dependencies + environment)
	$(call print_status,Running full system installation...)
	@if [ -x "./scripts/install.sh" ]; then \
		./scripts/install.sh; \
	else \
		$(call print_error,scripts/install.sh not found or not executable); \
		echo -e "$(FONT_YELLOW)Please ensure scripts/install.sh exists and is executable$(FONT_RESET)"; \
		exit 1; \
	fi

install-deps: install-full ## $(ROCKET) Alias for install-full

# ===========================================
# 🧪 Testing
# ===========================================
.PHONY: test test-unit test-mcp test-coverage
test: ## 🧪 Run all tests
	$(call print_status,Running all tests...)
	@$(UV) run pytest tests/ -v

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
		echo -e "$(FONT_RED)$(ERROR) Uncommitted changes detected!$(FONT_RESET)"; \
		echo -e "$(FONT_YELLOW)Please commit or stash your changes before publishing.$(FONT_RESET)"; \
		echo -e "$(FONT_CYAN)Run: git status$(FONT_RESET)"; \
		exit 1; \
	fi
	@# Check if on main branch
	@CURRENT_BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$CURRENT_BRANCH" != "main" ]; then \
		echo -e "$(FONT_YELLOW)$(WARNING) Not on main branch (current: $$CURRENT_BRANCH)$(FONT_RESET)"; \
		echo -e "$(FONT_YELLOW)It's recommended to publish from the main branch.$(FONT_RESET)"; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			exit 1; \
		fi; \
	fi
	@# Check if main branch is up to date with origin
	@git fetch origin main --quiet; \
	if [ "$$(git rev-parse HEAD)" != "$$(git rev-parse origin/main)" ]; then \
		echo -e "$(FONT_YELLOW)$(WARNING) Local main branch differs from origin/main$(FONT_RESET)"; \
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
	@if [ -z "$(TESTPYPI_TOKEN)" ]; then \
		$(call print_error,TESTPYPI_TOKEN not set); \
		echo -e "$(FONT_YELLOW)💡 Get your TestPyPI token at: https://test.pypi.org/manage/account/token/$(FONT_RESET)"; \
		echo -e "$(FONT_CYAN)💡 Set with: export TESTPYPI_TOKEN=pypi-xxxxx$(FONT_RESET)"; \
		exit 1; \
	fi
	@$(UV) run twine upload --repository testpypi dist/* -u __token__ -p "$(TESTPYPI_TOKEN)"
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
	$(UV) run twine upload dist/* -u __token__ -p "$(PYPI_TOKEN)"; \
	if ! git tag | grep -q "^v$$VERSION$$"; then \
		echo -e "$(FONT_CYAN)$(INFO) Creating git tag v$$VERSION$(FONT_RESET)"; \
		git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	fi; \
	echo -e "$(FONT_CYAN)$(INFO) Pushing tag to GitHub$(FONT_RESET)"; \
	git push origin "v$$VERSION"; \
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
# 🐳 Docker Commands
# ===========================================
.PHONY: docker-build docker-build-sse docker-build-http docker-build-stdio docker-run-sse docker-run-http docker-compose docker-deploy
docker-build: ## 🐳 Build all Docker images
	$(call print_status,Building all Docker images...)
	@$(MAKE) docker-build-sse
	@$(MAKE) docker-build-http
	@$(MAKE) docker-build-stdio
	$(call print_success,All Docker images built successfully!)

docker-build-sse: ## 🌊 Build SSE transport Docker image
	$(call print_status,Building SSE Docker image...)
	@docker build -f deploy/docker/Dockerfile.sse -t automagik-tools:sse .
	$(call print_success,SSE image built: automagik-tools:sse)

docker-build-http: ## 🌐 Build HTTP transport Docker image
	$(call print_status,Building HTTP Docker image...)
	@docker build -f deploy/docker/Dockerfile.http -t automagik-tools:http .
	$(call print_success,HTTP image built: automagik-tools:http)

docker-build-stdio: ## 💻 Build STDIO transport Docker image
	$(call print_status,Building STDIO Docker image...)
	@docker build -f deploy/docker/Dockerfile.stdio -t automagik-tools:stdio .
	$(call print_success,STDIO image built: automagik-tools:stdio)

docker-run-sse: ## 🚀 Run SSE server in Docker (PORT=8000)
	$(call print_status,Starting SSE server in Docker...)
	@$(call ensure_env_file)
	@docker run --rm -it \
		--env-file .env \
		-p ${PORT:-8000}:8000 \
		--name automagik-sse \
		automagik-tools:sse
		
docker-run-http: ## 🚀 Run HTTP server in Docker (PORT=8080)
	$(call print_status,Starting HTTP server in Docker...)
	@$(call ensure_env_file)
	@docker run --rm -it \
		--env-file .env \
		-p ${PORT:-8080}:8080 \
		--name automagik-http \
		automagik-tools:http

docker-compose: ## 🎼 Run multi-transport setup with docker-compose
	$(call print_status,Starting multi-transport Docker setup...)
	@$(call ensure_env_file)
	@docker-compose -f deploy/docker/docker-compose.yml up -d
	$(call print_success,Services started!)
	@echo -e "$(FONT_CYAN)📡 SSE server: http://localhost:8000$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)🌐 HTTP server: http://localhost:8080$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Stop with: docker-compose -f deploy/docker/docker-compose.yml down$(FONT_RESET)"

docker-deploy: ## 🚢 Deploy Docker container to cloud (PROVIDER=railway|aws|gcloud|render)
	$(call print_status,Deploying to cloud provider...)
	@if [ -z "$(PROVIDER)" ]; then \
		$(call print_error,PROVIDER not specified); \
		echo -e "$(FONT_YELLOW)Usage: make docker-deploy PROVIDER=railway$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)Available providers: railway, aws, gcloud, render$(FONT_RESET)"; \
		exit 1; \
	fi
	@$(UV) run python scripts/deploy_docker.py --provider $(PROVIDER)

# ===========================================
# 📈 Version Management
# ===========================================
.PHONY: bump-patch bump-minor bump-major bump-dev publish-dev finalize-version
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

bump-dev: ## 🧪 Create dev version (0.1.2 -> 0.1.2pre1, 0.1.2pre1 -> 0.1.2pre2)
	$(call print_status,Creating dev pre-release version...)
	@CURRENT_VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	if echo "$$CURRENT_VERSION" | grep -q "pre"; then \
		BASE_VERSION=$$(echo "$$CURRENT_VERSION" | cut -d'p' -f1); \
		PRE_NUM=$$(echo "$$CURRENT_VERSION" | sed 's/.*pre\([0-9]*\)/\1/'); \
		NEW_PRE_NUM=$$((PRE_NUM + 1)); \
		NEW_VERSION="$${BASE_VERSION}pre$${NEW_PRE_NUM}"; \
	else \
		NEW_VERSION="$${CURRENT_VERSION}pre1"; \
	fi; \
	sed -i "s/version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	echo -e "$(FONT_GREEN)✅ Dev version created: $$CURRENT_VERSION → $$NEW_VERSION$(FONT_RESET)"; \
	echo -e "$(FONT_CYAN)💡 Ready for: make publish-dev$(FONT_RESET)"

publish-dev: build check-dist ## 🚀 Build and publish dev version to PyPI
	$(call print_status,Publishing dev version to PyPI...)
	@CURRENT_VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	if ! echo "$$CURRENT_VERSION" | grep -q "pre"; then \
		$(call print_error,Not a dev version! Use 'make bump-dev' first); \
		echo -e "$(FONT_GRAY)Current version: $$CURRENT_VERSION$(FONT_RESET)"; \
		exit 1; \
	fi
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		$(call print_error,PYPI_TOKEN not set); \
		echo -e "$(FONT_YELLOW)💡 Get your PyPI token at: https://pypi.org/manage/account/token/$(FONT_RESET)"; \
		echo -e "$(FONT_CYAN)💡 Set with: export PYPI_TOKEN=pypi-xxxxx$(FONT_RESET)"; \
		exit 1; \
	fi
	@echo -e "$(FONT_CYAN)🚀 Publishing $$CURRENT_VERSION to PyPI for beta testing...$(FONT_RESET)"
	@$(UV) run twine upload dist/* -u __token__ -p "$(PYPI_TOKEN)"
	@echo -e "$(FONT_GREEN)✅ Dev version published to PyPI!$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Users can install with: pip install automagik-tools==$$CURRENT_VERSION$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Or latest pre-release: pip install --pre automagik-tools$(FONT_RESET)"

finalize-version: ## ✅ Remove 'pre' from version (0.1.2pre3 -> 0.1.2)
	$(call print_status,Finalizing version for release...)
	@CURRENT_VERSION=$$(grep "^version" pyproject.toml | cut -d'"' -f2); \
	if ! echo "$$CURRENT_VERSION" | grep -q "pre"; then \
		$(call print_error,Not a pre-release version!); \
		echo -e "$(FONT_GRAY)Current version: $$CURRENT_VERSION$(FONT_RESET)"; \
		exit 1; \
	fi; \
	FINAL_VERSION=$$(echo "$$CURRENT_VERSION" | cut -d'p' -f1); \
	sed -i "s/version = \"$$CURRENT_VERSION\"/version = \"$$FINAL_VERSION\"/" pyproject.toml; \
	echo -e "$(FONT_GREEN)✅ Version finalized: $$CURRENT_VERSION → $$FINAL_VERSION$(FONT_RESET)"; \
	echo -e "$(FONT_CYAN)💡 Ready for: make publish$(FONT_RESET)"

# ===========================================
# 🔧 System Service Management
# ===========================================
.PHONY: install-service start-service stop-service restart-service uninstall-service service-status

# Service configuration variables
SERVICE_NAME := automagik-tools

# ===========================================
# 🔧 Local PM2 Management (Standalone Mode)
# ===========================================
.PHONY: setup-pm2 start-local stop-local restart-local
setup-pm2: ## 📦 Setup local PM2 ecosystem
	$(call print_status,Setting up local PM2 ecosystem...)
	@$(call check_pm2)
	@echo -e "$(FONT_CYAN)$(INFO) Installing PM2 log rotation...$(FONT_RESET)"
	@if ! pm2 list | grep -q pm2-logrotate; then \
		pm2 install pm2-logrotate; \
	else \
		echo -e "$(FONT_GREEN)✓ PM2 logrotate already installed$(FONT_RESET)"; \
	fi
	@pm2 set pm2-logrotate:max_size 100M
	@pm2 set pm2-logrotate:retain 7
	@echo -e "$(FONT_CYAN)$(INFO) Setting up PM2 startup...$(FONT_RESET)"
	@if ! pm2 startup -s 2>/dev/null; then \
		echo -e "$(FONT_YELLOW)Warning: PM2 startup may already be configured$(FONT_RESET)"; \
	fi
	@$(call print_success,Local PM2 ecosystem configured!)

start-local: ## 🚀 Start service using local PM2 ecosystem
	$(call print_status,Starting automagik-tools with local PM2...)
	@$(call check_pm2)
	@if [ ! -d ".venv" ]; then \
		$(call print_error,Virtual environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@$(call ensure_env_file)
	@pm2 start ecosystem.config.js
	@$(call print_success,Service started with local PM2!)

stop-local: ## 🛑 Stop service using local PM2 ecosystem
	$(call print_status,Stopping automagik-tools with local PM2...)
	@$(call check_pm2)
	@pm2 stop automagik-tools 2>/dev/null || true
	@$(call print_success,Service stopped!)

restart-local: ## 🔄 Restart service using local PM2 ecosystem
	$(call print_status,Restarting automagik-tools with local PM2...)
	@$(call check_pm2)
	@pm2 restart automagik-tools 2>/dev/null || pm2 start ecosystem.config.js
	@$(call print_success,Service restarted!)

install-service: ## 🔧 Install local PM2 service for automagik-tools
	$(call print_status,Installing local PM2 service)
	@if [ ! -d ".venv" ]; then \
		$(call print_warning,Virtual environment not found - creating it now...); \
		$(MAKE) install; \
	fi
	@$(MAKE) setup-pm2
	@$(MAKE) start-local
	@$(call print_success,Local PM2 service installed!)

start-service: ## 🚀 Start local PM2 service
	@$(MAKE) start-local

stop-service: ## 🛑 Stop local PM2 service
	@$(MAKE) stop-local

restart-service: ## 🔄 Restart local PM2 service
	@$(MAKE) restart-local

uninstall-service: ## 🗑️ Uninstall local PM2 service
	$(call print_status,Uninstalling local PM2 service)
	@$(call check_pm2)
	@pm2 delete automagik-tools 2>/dev/null || true
	@pm2 save --force
	@$(call print_success,Local PM2 service uninstalled!)

define check_pm2
	@if ! command -v pm2 >/dev/null 2>&1; then \
		$(call print_error,PM2 not found. Install with: npm install -g pm2); \
		exit 1; \
	fi
endef

service-status: ## 📊 Check automagik-tools PM2 service status
	$(call print_status,Checking PM2 service status)
	@$(call check_pm2)
	@pm2 show automagik-tools 2>/dev/null || echo "Service not found"

.PHONY: logs logs-follow
logs: ## 📄 Show service logs (N=lines)
	$(eval N := $(or $(N),30))
	$(call print_status,Recent logs)
	@pm2 logs automagik-tools --lines $(N) --nostream 2>/dev/null || echo -e "$(FONT_YELLOW)⚠️ Service not found or not running$(FONT_RESET)"

logs-follow: ## 📄 Follow service logs in real-time
	$(call print_status,Following logs)
	@echo -e "$(FONT_YELLOW)Press Ctrl+C to stop following logs$(FONT_RESET)"
	@pm2 logs automagik-tools 2>/dev/null || echo -e "$(FONT_YELLOW)⚠️ Service not found or not running$(FONT_RESET)"

.PHONY: health
health: ## 🩺 Check service health endpoints
	$(call print_status,Checking automagik-tools health endpoints)
	@echo -e "$(FONT_CYAN)Testing SSE endpoint (port $(PORT)):$(FONT_RESET)"
	@curl -s http://$(HOST):$(PORT)/tools > /dev/null && \
		echo -e "  $(FONT_GREEN)✅ SSE endpoint responding$(FONT_RESET)" || \
		echo -e "  $(FONT_RED)❌ SSE endpoint not responding$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)Testing HTTP endpoint (port 8885):$(FONT_RESET)"
	@curl -s http://$(HOST):8885/tools > /dev/null && \
		echo -e "  $(FONT_GREEN)✅ HTTP endpoint responding$(FONT_RESET)" || \
		echo -e "  $(FONT_RED)❌ HTTP endpoint not responding$(FONT_RESET)"

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
.PHONY: list info run serve serve-all
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

serve: ## 🚀 Serve single tool (use TOOL=name TRANSPORT=stdio|sse|http)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make serve TOOL=<tool-name> [TRANSPORT=stdio|sse|http]); \
		echo -e "$(FONT_GRAY)Example: make serve TOOL=evolution-api TRANSPORT=stdio$(FONT_RESET)"; \
		exit 1; \
	fi
	$(call print_status,Starting $(TOOL) with $(or $(TRANSPORT),stdio) transport...)
	@$(call ensure_env_file)
	@$(UV) run automagik-tools tool $(TOOL) --transport $(or $(TRANSPORT),stdio) --host $(HOST) --port $(PORT)

serve-all: ## 🌐 Serve all tools on single server (hub SSE)
	$(call print_status,Starting multi-tool hub server on $(HOST):$(PORT)...)
	@$(UV) run automagik-tools hub --host $(HOST) --port $(PORT) --transport sse

serve-dual: ## 🌐 Serve all tools on dual transports (SSE:8884 + HTTP:8885)
	$(call print_status,Starting dual-transport hub servers...)
	$(call print_info,SSE server: $(HOST):$(PORT))
	$(call print_info,HTTP server: $(HOST):8885)
	@$(UV) run automagik-tools hub --host $(HOST) --port $(PORT) --transport sse & \
	$(UV) run automagik-tools hub --host $(HOST) --port 8885 --transport http & \
	wait

# ===========================================
# 🌐 HTTP Development Deployment
# ===========================================
.PHONY: http-start http-stop http-restart http-status http-logs http-dev http-network
http-start: ## 🌐 Start HTTP development server (HOST=0.0.0.0 PORT=8000 TOOLS=all)
	$(call print_status,Starting HTTP development server...)
	@./scripts/deploy_http_dev.sh start $(or $(HOST),0.0.0.0) $(or $(PORT),8000) $(or $(TOOLS),all)

http-stop: ## 🛑 Stop HTTP development server (PORT=8000)
	$(call print_status,Stopping HTTP development server...)
	@./scripts/deploy_http_dev.sh stop $(or $(PORT),8000)

http-restart: ## 🔄 Restart HTTP development server
	$(call print_status,Restarting HTTP development server...)
	@./scripts/deploy_http_dev.sh restart $(or $(HOST),0.0.0.0) $(or $(PORT),8000) $(or $(TOOLS),all)

http-status: ## 📊 Check HTTP server status (PORT=8000)
	@./scripts/deploy_http_dev.sh status $(or $(PORT),8000)

http-logs: ## 📋 Show HTTP server logs (PORT=8000)
	@./scripts/deploy_http_dev.sh logs $(or $(PORT),8000)

http-dev: ## 🚀 Quick development setup (localhost:8000)
	$(call print_status,Starting HTTP development setup...)
	@./scripts/deploy_http_dev.sh dev

http-network: ## 🌐 Network accessible setup (0.0.0.0:8000)
	$(call print_status,Starting HTTP network setup...)
	@./scripts/deploy_http_dev.sh network

# ===========================================
# 🔧 Tool Creation
# ===========================================
.PHONY: tool new-tool test-tool validate-tool
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

new-tool: ## 🔧 Create new tool interactively
	$(call print_status,Creating new tool interactively...)
	@$(UV) run python scripts/create_tool.py
	$(call print_success,Tool created successfully!)

test-tool: ## 🧪 Test specific tool (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make test-tool TOOL=<tool-name>); \
		echo -e "$(FONT_GRAY)Example: make test-tool TOOL=evolution-api$(FONT_RESET)"; \
		exit 1; \
	fi
	$(call print_status,Testing tool: $(TOOL)...)
	@$(UV) run pytest tests/tools/test_$(TOOL).py -v

validate-tool: ## ✅ Validate tool compliance (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make validate-tool TOOL=<tool-name>); \
		echo -e "$(FONT_GRAY)Example: make validate-tool TOOL=evolution-api$(FONT_RESET)"; \
		exit 1; \
	fi
	$(call print_status,Validating tool: $(TOOL)...)
	@if [ -f "scripts/validate_tool.py" ]; then \
		$(UV) run python scripts/validate_tool.py $(TOOL); \
	else \
		$(call print_warning,Validation script not yet implemented); \
		echo -e "$(FONT_YELLOW)Tool validation framework coming soon!$(FONT_RESET)"; \
	fi

# ===========================================
# 🔥 Development
# ===========================================
.PHONY: dev-server
dev-server: ## 🔥 Start development server with hot-reload
	$(call print_status,Starting development server with hot-reload...)
	@$(UV) run watchmedo auto-restart \
		--directory automagik_tools \
		--pattern "*.py" \
		--recursive \
		-- make serve-all HOST=$(HOST) PORT=$(PORT)

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
# 🔧 MCP Configuration
# ===========================================
.PHONY: mcp-config
mcp-config: ## 🔧 Generate MCP configuration for Cursor/Claude (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		echo -e "$(FONT_RED)$(ERROR) Usage: make mcp-config TOOL=<tool-name>$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)Example: make mcp-config TOOL=automagik-agents$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)Example: make mcp-config TOOL=discord-api$(FONT_RESET)"; \
		exit 1; \
	fi
	@echo -e "$(FONT_CYAN)$(STATUS) Generating MCP configuration for $(TOOL)...$(FONT_RESET)"
	@$(UV) run automagik-tools mcp-config $(TOOL)

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