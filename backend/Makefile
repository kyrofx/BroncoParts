# Makefile for Bronco Parts Backend Tests

.PHONY: test test-unit test-integration test-coverage test-html test-fast install clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-html      - Run tests with HTML coverage report"
	@echo "  test-fast      - Run tests in fast mode (no coverage)"
	@echo "  install        - Install test dependencies"
	@echo "  clean          - Clean test artifacts"
	@echo "  lint           - Run code linting (if configured)"

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	python run_tests.py

# Run unit tests only
test-unit:
	python run_tests.py --unit

# Run integration tests only
test-integration:
	python run_tests.py --integration

# Run tests with coverage
test-coverage:
	python run_tests.py --coverage

# Run tests with HTML coverage report
test-html:
	python run_tests.py --html

# Run fast tests
test-fast:
	python run_tests.py --fast

# Clean test artifacts
clean:
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run linting (add your preferred linter)
lint:
	@echo "Configure your preferred linter (flake8, pylint, black, etc.)"

# Development workflow - install and test
dev-setup: install test

# CI workflow - install, test with coverage, and generate reports
ci: install test-coverage
