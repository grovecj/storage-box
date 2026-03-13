#!/bin/bash
# Test script for validating CI tooling configuration and execution
# This script runs all linting, type checking, and testing tools to verify
# that Ticket #34 acceptance criteria are met.

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Track overall status
FAILED=0

# ============================================================================
# BACKEND TESTS
# ============================================================================

print_header "Backend: Ruff Linting"
if docker compose exec -T backend ruff check app/; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed"
    FAILED=1
fi

print_header "Backend: Mypy Type Checking"
if docker compose exec -T backend mypy app/; then
    print_success "Mypy type checking passed"
else
    print_error "Mypy type checking failed"
    FAILED=1
fi

print_header "Backend: Pytest with Coverage Gate"
if docker compose exec -T backend pytest --tb=short -q --cov=app --cov-report=term-missing --cov-fail-under=80; then
    print_success "Backend tests passed with 80% coverage"
else
    print_error "Backend tests or coverage gate failed"
    FAILED=1
fi

print_header "Backend: CI Configuration Tests"
if docker compose exec -T backend pytest tests/test_ci_config.py -v; then
    print_success "CI configuration tests passed"
else
    print_error "CI configuration tests failed"
    FAILED=1
fi

# ============================================================================
# FRONTEND TESTS
# ============================================================================

print_header "Frontend: TypeScript Type Checking"
cd /home/carter/dev/storage-box/frontend
if npm run typecheck; then
    print_success "TypeScript type checking passed"
else
    print_error "TypeScript type checking failed"
    FAILED=1
fi

print_header "Frontend: ESLint"
if npm run lint; then
    print_success "ESLint passed"
else
    print_error "ESLint failed"
    FAILED=1
fi

print_header "Frontend: Build"
if npm run build 2>&1 | tail -10; then
    print_success "Frontend build passed"
else
    print_error "Frontend build failed"
    FAILED=1
fi

# ============================================================================
# CONFIGURATION FILE VALIDATION
# ============================================================================

print_header "Validating Configuration Files"

cd /home/carter/dev/storage-box

# Check backend configuration files
if [ -f "backend/pyproject.toml" ]; then
    print_success "backend/pyproject.toml exists"

    if grep -q "\[tool.ruff\]" backend/pyproject.toml; then
        print_success "Ruff configuration present"
    else
        print_error "Ruff configuration missing"
        FAILED=1
    fi

    if grep -q "\[tool.mypy\]" backend/pyproject.toml; then
        print_success "Mypy configuration present"
    else
        print_error "Mypy configuration missing"
        FAILED=1
    fi
else
    print_error "backend/pyproject.toml not found"
    FAILED=1
fi

if grep -q "ruff==" backend/requirements.txt; then
    print_success "ruff in requirements.txt"
else
    print_error "ruff missing from requirements.txt"
    FAILED=1
fi

if grep -q "mypy==" backend/requirements.txt; then
    print_success "mypy in requirements.txt"
else
    print_error "mypy missing from requirements.txt"
    FAILED=1
fi

# Check frontend configuration files
if [ -f "frontend/eslint.config.js" ]; then
    print_success "frontend/eslint.config.js exists"

    if grep -q "typescript-eslint" frontend/eslint.config.js; then
        print_success "TypeScript ESLint plugin configured"
    else
        print_error "TypeScript ESLint plugin not configured"
        FAILED=1
    fi

    if grep -q "react-hooks" frontend/eslint.config.js; then
        print_success "React hooks plugin configured"
    else
        print_error "React hooks plugin not configured"
        FAILED=1
    fi
else
    print_error "frontend/eslint.config.js not found"
    FAILED=1
fi

if grep -q '"lint"' frontend/package.json; then
    print_success "npm lint script configured"
else
    print_error "npm lint script missing"
    FAILED=1
fi

if grep -q '"typecheck"' frontend/package.json; then
    print_success "npm typecheck script configured"
else
    print_error "npm typecheck script missing"
    FAILED=1
fi

# Check CI workflow
if [ -f ".github/workflows/ci.yml" ]; then
    print_success ".github/workflows/ci.yml exists"

    if grep -q "ruff check" .github/workflows/ci.yml; then
        print_success "CI runs ruff check"
    else
        print_error "CI doesn't run ruff check"
        FAILED=1
    fi

    if grep -q "run: mypy" .github/workflows/ci.yml; then
        print_success "CI runs mypy"
    else
        print_error "CI doesn't run mypy"
        FAILED=1
    fi

    if grep -q "npm run typecheck" .github/workflows/ci.yml; then
        print_success "CI runs TypeScript type checking"
    else
        print_error "CI doesn't run TypeScript type checking"
        FAILED=1
    fi

    if grep -q "npm run lint" .github/workflows/ci.yml; then
        print_success "CI runs ESLint"
    else
        print_error "CI doesn't run ESLint"
        FAILED=1
    fi

    if grep -q -- "--cov-fail-under=80" .github/workflows/ci.yml; then
        print_success "CI enforces 80% coverage gate"
    else
        print_error "CI doesn't enforce 80% coverage gate"
        FAILED=1
    fi
else
    print_error ".github/workflows/ci.yml not found"
    FAILED=1
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "Test Summary"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Acceptance Criteria Met:"
    echo "  ✓ ESLint added to frontend CI job"
    echo "  ✓ Ruff added to backend CI job"
    echo "  ✓ mypy type checking for backend"
    echo "  ✓ tsc --noEmit as separate frontend CI step"
    echo "  ✓ All checks pass on current codebase"
    echo ""
    exit 0
else
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}SOME TESTS FAILED${NC}"
    echo -e "${RED}============================================${NC}"
    exit 1
fi
