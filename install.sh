#!/bin/bash
# VidCollector Installation Script for Ubuntu 24.04
# This script sets up VidCollector with UV package manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Ubuntu
check_ubuntu() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot detect OS. This script is designed for Ubuntu 24.04."
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        print_warning "This script is optimized for Ubuntu. Detected: $ID"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    if [[ "$VERSION_ID" != "24.04" ]]; then
        print_warning "This script is optimized for Ubuntu 24.04. Detected: $VERSION_ID"
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        curl \
        wget \
        git \
        ffmpeg \
        sqlite3 \
        libsqlite3-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        libjpeg-dev \
        libpng-dev \
        libffi-dev \
        libssl-dev \
        make
    
    print_success "System dependencies installed"
}

# Install UV package manager
install_uv() {
    print_status "Installing UV package manager..."
    
    if command -v uv >/dev/null 2>&1; then
        print_success "UV is already installed ($(uv --version))"
        return 0
    fi
    
    # Install UV
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if command -v uv >/dev/null 2>&1; then
        print_success "UV installed successfully ($(uv --version))"
    else
        print_error "UV installation failed"
        exit 1
    fi
}

# Install project dependencies
install_project_deps() {
    print_status "Installing VidCollector dependencies..."
    
    # Ensure we're in the project directory
    if [[ ! -f "pyproject.toml" ]]; then
        print_error "pyproject.toml not found. Please run this script from the VidCollector directory."
        exit 1
    fi
    
    # Install dependencies
    uv sync
    
    print_success "Project dependencies installed"
}

# Install development dependencies
install_dev_deps() {
    print_status "Installing development dependencies..."
    uv sync --extra dev --extra test --extra docs
    print_success "Development dependencies installed"
}

# Setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please edit .env and add your YouTube API key"
        else
            print_warning ".env.example not found"
        fi
    else
        print_success ".env file already exists"
    fi
}

# Run tests to verify installation
run_tests() {
    print_status "Running tests to verify installation..."
    
    if uv run python -m unittest tests.test_basic -v; then
        print_success "All tests passed!"
    else
        print_warning "Some tests failed, but installation should still work"
    fi
}

# Run demo
run_demo() {
    print_status "Running demo..."
    
    if uv run python example_usage.py; then
        print_success "Demo completed successfully!"
    else
        print_error "Demo failed"
    fi
}

# Main installation function
main() {
    echo "🚀 VidCollector Installation Script for Ubuntu 24.04"
    echo "=================================================="
    echo
    
    # Parse command line arguments
    INSTALL_DEV=false
    RUN_TESTS=false
    RUN_DEMO=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                INSTALL_DEV=true
                shift
                ;;
            --test)
                RUN_TESTS=true
                shift
                ;;
            --demo)
                RUN_DEMO=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --dev     Install development dependencies"
                echo "  --test    Run tests after installation"
                echo "  --demo    Run demo after installation"
                echo "  --help    Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Check Ubuntu version
    check_ubuntu
    
    # Install system dependencies
    install_system_deps
    
    # Install UV
    install_uv
    
    # Install project dependencies
    if [[ "$INSTALL_DEV" == true ]]; then
        install_dev_deps
    else
        install_project_deps
    fi
    
    # Setup configuration
    setup_config
    
    # Run tests if requested
    if [[ "$RUN_TESTS" == true ]]; then
        run_tests
    fi
    
    # Run demo if requested
    if [[ "$RUN_DEMO" == true ]]; then
        run_demo
    fi
    
    echo
    print_success "🎉 VidCollector installation completed!"
    echo
    echo "Next steps:"
    echo "1. Edit .env and add your YouTube API key"
    echo "2. Run 'make run-demo' to test the installation"
    echo "3. Run 'make crawl' to start crawling (requires API key)"
    echo "4. Run 'make help' to see all available commands"
    echo
    echo "For development:"
    echo "- Run '$0 --dev' to install development dependencies"
    echo "- Use 'make format' and 'make lint' for code quality"
    echo "- Use 'make test' to run the test suite"
}

# Run main function
main "$@"