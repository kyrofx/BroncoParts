#!/usr/bin/env python
"""
Test runner script for the Bronco Parts backend application.
Provides convenient commands for running different types of tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and return the result."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {cmd}")
        print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run tests for Bronco Parts backend")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests") 
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--fast", action="store_true", help="Run tests in fast mode (no coverage)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", "-f", help="Run tests from specific file")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (requires pytest-xdist)")
    
    args = parser.parse_args()
    
    # Change to the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Build pytest command
    cmd_parts = ["python3", "-m", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd_parts.extend(["-m", "unit"])
    elif args.integration:
        cmd_parts.extend(["-m", "integration"])
    elif args.file:
        cmd_parts.append(args.file)
    else:
        cmd_parts.append("tests/")
    
    # Add options
    if args.verbose:
        cmd_parts.append("-v")
    
    if args.pattern:
        cmd_parts.extend(["-k", args.pattern])
    
    if args.parallel:
        cmd_parts.extend(["-n", str(args.parallel)])
    
    if args.fast:
        # Fast mode - no coverage
        cmd_parts.extend(["--tb=short", "-q"])
    elif args.coverage or args.html:
        # Coverage mode
        cmd_parts.extend([
            "--cov=app",
            "--cov-report=term-missing"
        ])
        if args.html:
            cmd_parts.append("--cov-report=html")
    
    # Run the tests
    cmd = " ".join(cmd_parts)
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n✅ All tests passed!")
        if args.html and (args.coverage or args.html):
            print("📊 HTML coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
