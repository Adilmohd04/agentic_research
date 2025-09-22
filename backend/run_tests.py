#!/usr/bin/env python3
"""
Comprehensive test runner for the Agentic Research Copilot backend.

This script runs all tests with proper categorization and reporting.
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    success = True
    
    if args.unit:
        # Run unit tests
        cmd = pytest_cmd + ["-m", "unit", "tests/"]
        success &= run_command(cmd, "Unit Tests")
    
    elif args.integration:
        # Run integration tests
        cmd = pytest_cmd + ["-m", "integration", "tests/"]
        success &= run_command(cmd, "Integration Tests")
    
    elif args.performance:
        # Run performance tests
        cmd = pytest_cmd + ["tests/test_performance.py"]
        success &= run_command(cmd, "Performance Tests")
    
    else:
        # Run all tests by category
        test_categories = [
            ("Authentication Tests", ["-m", "auth", "tests/test_auth*.py"]),
            ("Agent Tests", ["tests/test_*agent*.py", "tests/test_agents.py"]),
            ("RAG System Tests", ["tests/test_rag*.py"]),
            ("MCP Integration Tests", ["tests/test_mcp.py"]),
            ("Voice Interface Tests", ["tests/test_*tt*.py"]),
            ("Security Tests", ["tests/test_*security*.py", "tests/test_encryption.py"]),
            ("Performance Tests", ["tests/test_performance.py"]),
            ("Error Handling Tests", ["tests/test_error*.py"]),
            ("Memory Management Tests", ["tests/test_memory.py"]),
            ("WebSocket Tests", ["tests/test_websocket.py"]),
        ]
        
        for description, test_args in test_categories:
            cmd = pytest_cmd + test_args
            success &= run_command(cmd, description)
    
    if args.coverage:
        # Generate coverage report
        coverage_cmd = ["python", "-m", "coverage", "html"]
        run_command(coverage_cmd, "Coverage Report Generation")
        print("\nCoverage report generated in htmlcov/index.html")
    
    # Final summary
    print(f"\n{'='*60}")
    if success:
        print("✅ ALL TESTS PASSED!")
        print("The Agentic Research Copilot backend is ready for deployment.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please review the test failures above.")
        sys.exit(1)
    print(f"{'='*60}")

if __name__ == "__main__":
    main()