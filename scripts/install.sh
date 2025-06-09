#!/bin/bash

# ========================================
# AutoMagik Tools - Universal Installer
# ========================================
# Detects OS and installs all dependencies including:
# - Python 3.10+ 
# - uv (Python package manager)
# - make (build tool)
# - git (version control)
# - curl (for downloads)
# - And sets up the development environment

set -e  # Exit on any error

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
FONT_RED=$(tput setaf 1 2>/dev/null || echo "")
FONT_GREEN=$(tput setaf 2 2>/dev/null || echo "")
FONT_YELLOW=$(tput setaf 3 2>/dev/null || echo "")
FONT_BLUE=$(tput setaf 4 2>/dev/null || echo "")
FONT_PURPLE=$(tput setaf 5 2>/dev/null || echo "")
FONT_CYAN=$(tput setaf 6 2>/dev/null || echo "")
FONT_GRAY=$(tput setaf 7 2>/dev/null || echo "")
FONT_BOLD=$(tput bold 2>/dev/null || echo "")
FONT_RESET=$(tput sgr0 2>/dev/null || echo "")

CHECKMARK="✅"
WARNING="⚠️"
ERROR="❌"
ROCKET="🚀"
TOOLS="🛠️"
INFO="ℹ️"
SPARKLES="✨"

# ===========================================
# 🛠️ Utility Functions
# ===========================================
print_status() {
    echo -e "${FONT_PURPLE}${TOOLS} $1${FONT_RESET}"
}

print_success() {
    echo -e "${FONT_GREEN}${CHECKMARK} $1${FONT_RESET}"
}

print_warning() {
    echo -e "${FONT_YELLOW}${WARNING} $1${FONT_RESET}"
}

print_error() {
    echo -e "${FONT_RED}${ERROR} $1${FONT_RESET}"
}

print_info() {
    echo -e "${FONT_CYAN}${INFO} $1${FONT_RESET}"
}

show_automagik_logo() {
    echo ""
    echo -e "${FONT_PURPLE}     -+*         -=@%*@@@@@@*  -#@@@%*  =@@*      -%@#+   -*       +%@@@@*-%@*-@@*  -+@@*   ${FONT_RESET}"
    echo -e "${FONT_PURPLE}     =@#*  -@@*  -=@%+@@@@@@*-%@@#%*%@@+=@@@*    -+@@#+  -@@*   -#@@%%@@@*-%@+-@@* -@@#*    ${FONT_RESET}"
    echo -e "${FONT_PURPLE}    -%@@#* -@@*  -=@@* -@%* -@@**   --@@=@@@@*  -+@@@#+ -#@@%* -*@%*-@@@@*-%@+:@@+#@@*      ${FONT_RESET}"
    echo -e "${FONT_PURPLE}   -#@+%@* -@@*  -=@@* -@%* -@@*-+@#*-%@+@@=@@* +@%#@#+ =@##@* -%@#*-@@@@*-%@+-@@@@@*       ${FONT_RESET}"
    echo -e "${FONT_PURPLE}  -*@#==@@*-@@*  -+@%* -@%* -%@#*   -+@@=@@++@%-@@=*@#=-@@*-@@*:+@@*  -%@*-%@+-@@#*@@**     ${FONT_RESET}"
    echo -e "${FONT_PURPLE}  -@@* -+@%-+@@@@@@@*  -@%*  -#@@@@%@@%+=@@+-=@@@*    -%@*  -@@*-*@@@@%@@*#@@#=%*  -%@@*    ${FONT_RESET}"
    echo -e "${FONT_PURPLE} -@@*+  -%@*  -#@%+    -@%+     =#@@*   =@@+          +@%+  -#@#   -*%@@@*@@@@%+     =@@+   ${FONT_RESET}"
    echo ""
}

# ===========================================
# 🔍 OS Detection
# ===========================================
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
        elif [ -f /etc/arch-release ]; then
            OS="arch"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    
    print_info "Detected OS: $OS"
}

# ===========================================
# 🐍 Python Installation
# ===========================================
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            print_success "Python $PYTHON_VERSION found (requirement: 3.10+)"
            return 0
        else
            print_warning "Python $PYTHON_VERSION found but requirement is 3.10+"
        fi
    else
        print_warning "Python 3 not found"
    fi
    
    print_status "Installing Python 3.10+..."
    install_python
}

install_python() {
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv python3-dev
            ;;
        "redhat")
            sudo yum install -y python3 python3-pip python3-devel
            ;;
        "arch")
            sudo pacman -S --noconfirm python python-pip
            ;;
        "macos")
            if command -v brew >/dev/null 2>&1; then
                brew install python@3.11
            else
                print_error "Homebrew not found. Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                brew install python@3.11
            fi
            ;;
        "windows")
            print_error "Please install Python 3.10+ from python.org or Microsoft Store"
            exit 1
            ;;
        *)
            print_error "Unsupported OS for automatic Python installation"
            print_info "Please install Python 3.10+ manually from python.org"
            exit 1
            ;;
    esac
    
    print_success "Python installation completed"
}

# ===========================================
# 📦 UV Installation
# ===========================================
check_uv() {
    print_status "Checking uv installation..."
    
    # Check if uv is already available in PATH
    if command -v uv >/dev/null 2>&1; then
        UV_VERSION=$(uv --version | cut -d' ' -f2)
        print_success "uv $UV_VERSION found"
        return 0
    fi
    
    # Check if uv exists in common locations but not in PATH
    UV_PATHS=(
        "$HOME/.cargo/bin/uv"
        "$HOME/.local/bin/uv"
        "/usr/local/bin/uv"
    )
    
    for uv_path in "${UV_PATHS[@]}"; do
        if [ -f "$uv_path" ]; then
            UV_VERSION=$("$uv_path" --version | cut -d' ' -f2)
            print_success "uv $UV_VERSION found at $uv_path"
            export PATH="$(dirname "$uv_path"):$PATH"
            return 0
        fi
    done
    
    print_status "Installing uv (Python package manager)..."
    install_uv
}

install_uv() {
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        print_error "Neither curl nor wget found. Please install one of them first."
        exit 1
    fi
    
    # Smart PATH reloading - try multiple possible locations
    UV_PATHS=(
        "$HOME/.cargo/bin/uv"
        "$HOME/.local/bin/uv"
        "/usr/local/bin/uv"
    )
    
    UV_FOUND=""
    for uv_path in "${UV_PATHS[@]}"; do
        if [ -f "$uv_path" ]; then
            UV_FOUND="$uv_path"
            export PATH="$(dirname "$uv_path"):$PATH"
            break
        fi
    done
    
    # Force reload environment
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc" 2>/dev/null || true
    fi
    if [ -f "$HOME/.zshrc" ]; then
        source "$HOME/.zshrc" 2>/dev/null || true
    fi
    if [ -f "$HOME/.profile" ]; then
        source "$HOME/.profile" 2>/dev/null || true
    fi
    
    # Test if uv is now available
    if command -v uv >/dev/null 2>&1; then
        print_success "uv installed and available"
        return 0
    elif [ -n "$UV_FOUND" ]; then
        print_success "uv installed at $UV_FOUND"
        # Create a function to use the full path
        uv() {
            "$UV_FOUND" "$@"
        }
        export -f uv
        return 0
    else
        print_error "uv installation failed or not found in expected locations"
        print_info "Trying to add to current shell PATH..."
        export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
        
        if command -v uv >/dev/null 2>&1; then
            print_success "uv now available via PATH update"
            return 0
        else
            print_error "Could not make uv available. Manual intervention required."
            return 1
        fi
    fi
}

# ===========================================
# 🔨 Make Installation
# ===========================================
check_make() {
    print_status "Checking make installation..."
    
    if command -v make >/dev/null 2>&1; then
        MAKE_VERSION=$(make --version | head -n1)
        print_success "make found: $MAKE_VERSION"
        return 0
    fi
    
    print_status "Installing make..."
    install_make
}

install_make() {
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y build-essential
            ;;
        "redhat")
            sudo yum groupinstall -y "Development Tools"
            ;;
        "arch")
            sudo pacman -S --noconfirm base-devel
            ;;
        "macos")
            if command -v brew >/dev/null 2>&1; then
                brew install make
            else
                # Xcode Command Line Tools includes make
                xcode-select --install
            fi
            ;;
        "windows")
            print_error "Please install make via Chocolatey: choco install make"
            print_info "Or install via MSYS2/MinGW"
            exit 1
            ;;
        *)
            print_error "Unsupported OS for automatic make installation"
            exit 1
            ;;
    esac
    
    print_success "make installation completed"
}

# ===========================================
# 🌐 Git Installation
# ===========================================
check_git() {
    print_status "Checking git installation..."
    
    if command -v git >/dev/null 2>&1; then
        GIT_VERSION=$(git --version)
        print_success "git found: $GIT_VERSION"
        return 0
    fi
    
    print_status "Installing git..."
    install_git
}

install_git() {
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y git
            ;;
        "redhat")
            sudo yum install -y git
            ;;
        "arch")
            sudo pacman -S --noconfirm git
            ;;
        "macos")
            if command -v brew >/dev/null 2>&1; then
                brew install git
            else
                xcode-select --install
            fi
            ;;
        "windows")
            print_error "Please install Git from git-scm.com"
            exit 1
            ;;
        *)
            print_error "Unsupported OS for automatic git installation"
            exit 1
            ;;
    esac
    
    print_success "git installation completed"
}

# ===========================================
# 📡 Curl Installation
# ===========================================
check_curl() {
    print_status "Checking curl installation..."
    
    if command -v curl >/dev/null 2>&1; then
        CURL_VERSION=$(curl --version | head -n1)
        print_success "curl found: $CURL_VERSION"
        return 0
    fi
    
    print_status "Installing curl..."
    install_curl
}

install_curl() {
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y curl
            ;;
        "redhat")
            sudo yum install -y curl
            ;;
        "arch")
            sudo pacman -S --noconfirm curl
            ;;
        "macos")
            # curl is usually pre-installed on macOS
            if command -v brew >/dev/null 2>&1; then
                brew install curl
            fi
            ;;
        "windows")
            print_info "curl is usually pre-installed on Windows 10+"
            ;;
        *)
            print_warning "Unable to install curl automatically"
            ;;
    esac
    
    print_success "curl installation completed"
}

# ===========================================
# 🔧 Environment Setup
# ===========================================
setup_environment() {
    print_status "Setting up AutoMagik Tools environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_info "Creating .env file from example..."
        cp .env.example .env
        print_success ".env created from example"
        print_warning "Please edit .env and add your API keys"
    else
        print_info ".env file already exists"
    fi
    
    # Install Python dependencies with uv
    print_status "Installing Python dependencies with uv..."
    
    # Ensure uv is available - try multiple approaches
    if ! command -v uv >/dev/null 2>&1; then
        print_warning "uv not in PATH, attempting to locate and use..."
        
        # Try to find uv in common locations
        UV_PATHS=(
            "$HOME/.cargo/bin/uv"
            "$HOME/.local/bin/uv"
            "/usr/local/bin/uv"
        )
        
        UV_CMD=""
        for uv_path in "${UV_PATHS[@]}"; do
            if [ -f "$uv_path" ]; then
                UV_CMD="$uv_path"
                break
            fi
        done
        
        if [ -n "$UV_CMD" ]; then
            print_info "Found uv at: $UV_CMD"
            "$UV_CMD" sync --all-extras
            print_success "Dependencies installed successfully with $UV_CMD"
        else
            print_error "uv not found in any expected location."
            print_info "Please ensure uv is installed correctly and try again."
            print_info "You can install uv manually with: curl -LsSf https://astral.sh/uv/install.sh | sh"
            return 1
        fi
    else
        uv sync --all-extras
        print_success "Dependencies installed successfully"
    fi
}

# ===========================================
# 🧪 Verification
# ===========================================
verify_installation() {
    print_status "Verifying installation..."
    
    # Find uv command
    UV_CMD="uv"
    if ! command -v uv >/dev/null 2>&1; then
        # Try to find uv in common locations
        UV_PATHS=(
            "$HOME/.cargo/bin/uv"
            "$HOME/.local/bin/uv"
            "/usr/local/bin/uv"
        )
        
        for uv_path in "${UV_PATHS[@]}"; do
            if [ -f "$uv_path" ]; then
                UV_CMD="$uv_path"
                break
            fi
        done
    fi
    
    # Test basic CLI functionality
    if [ -x "$UV_CMD" ] || command -v "$UV_CMD" >/dev/null 2>&1; then
        if "$UV_CMD" run automagik-tools version >/dev/null 2>&1; then
            print_success "AutoMagik Tools CLI is working"
        else
            print_warning "AutoMagik Tools CLI test failed"
        fi
        
        if "$UV_CMD" run automagik-tools list >/dev/null 2>&1; then
            print_success "Tool discovery is working"
        else
            print_warning "Tool discovery test failed"
        fi
    else
        print_warning "Cannot verify - uv not found"
    fi
}

# ===========================================
# 📋 Usage Information
# ===========================================
show_usage_info() {
    # Find the correct uv path for user instructions
    UV_PATH="uv"
    if ! command -v uv >/dev/null 2>&1; then
        UV_CANDIDATES=(
            "$HOME/.cargo/bin/uv"
            "$HOME/.local/bin/uv"
            "/usr/local/bin/uv"
        )
        
        for candidate in "${UV_CANDIDATES[@]}"; do
            if [ -f "$candidate" ]; then
                UV_PATH="$candidate"
                break
            fi
        done
    fi
    
    echo ""
    echo -e "${FONT_CYAN}${SPARKLES} AutoMagik Tools Installation Complete! ${SPARKLES}${FONT_RESET}"
    echo ""
    
    if [ "$UV_PATH" != "uv" ]; then
        echo -e "${FONT_YELLOW}⚠️ Note: uv not in PATH. Add to your shell profile:${FONT_RESET}"
        echo -e "  ${FONT_GRAY}export PATH=\"$(dirname "$UV_PATH"):\$PATH\"${FONT_RESET}"
        echo ""
    fi
    
    echo -e "${FONT_YELLOW}Quick Start Commands:${FONT_RESET}"
    echo -e "  ${FONT_PURPLE}${UV_PATH} run automagik-tools list${FONT_RESET}                    # List available tools"
    echo -e "  ${FONT_PURPLE}${UV_PATH} run automagik-tools serve --tool automagik${FONT_RESET}  # Start automagik tool"
    echo -e "  ${FONT_PURPLE}make help${FONT_RESET}                                      # Show all available commands"
    echo ""
    echo -e "${FONT_YELLOW}Development Commands:${FONT_RESET}"
    echo -e "  ${FONT_PURPLE}make test${FONT_RESET}                                      # Run tests"
    echo -e "  ${FONT_PURPLE}make serve-all${FONT_RESET}                               # Serve all tools"
    echo -e "  ${FONT_PURPLE}make format${FONT_RESET}                                   # Format code"
    echo ""
    echo -e "${FONT_YELLOW}Deploy Any API:${FONT_RESET}"
    echo -e "  ${FONT_PURPLE}${UV_PATH} run automagik-tools serve --openapi-url https://api.example.com/openapi.json${FONT_RESET}"
    echo ""
    echo -e "${FONT_GRAY}📖 Documentation: https://github.com/namastexlabs/automagik-tools${FONT_RESET}"
    echo -e "${FONT_GRAY}💬 Issues: https://github.com/namastexlabs/automagik-tools/issues${FONT_RESET}"
    echo ""
}

# ===========================================
# 🚀 Main Installation Flow
# ===========================================
main() {
    show_automagik_logo
    echo -e "${FONT_BOLD}${FONT_PURPLE}🛠️ AutoMagik Tools Universal Installer${FONT_RESET}"
    echo -e "${FONT_GRAY}Installing all dependencies for MCP tool development${FONT_RESET}"
    echo ""
    
    detect_os
    echo ""
    
    # Check and install core dependencies
    check_curl
    check_git
    check_python
    check_uv
    check_make
    echo ""
    
    # Setup project environment
    setup_environment
    echo ""
    
    # Verify everything works
    verify_installation
    echo ""
    
    # Show usage information
    show_usage_info
    
    print_success "Installation completed successfully!"
    print_info "Ready to build MCP tools! 🚀"
}

# Run the installer
main "$@"