"""Test execution tools for the test generator agent."""

import os
import py_compile
import subprocess
import sys

from config import TEST_OUTPUT_DIR, CLONED_PROJECT_DIR


def run_tests(test_file_path: str) -> str:
    """Execute pytest on a test file and return results.

    Runs pytest in an isolated environment: the working directory is set
    to the tests/ folder, and PYTHONPATH only includes the tests/ dir
    (not the cloned project) to avoid import conflicts when testing
    projects that shadow installed packages (e.g. testing pytest itself).

    Args:
        test_file_path: Path to the test file to run.

    Returns:
        Combined stdout/stderr output and exit code from pytest.
    """
    try:
        abs_path = os.path.abspath(test_file_path)
        if not os.path.exists(abs_path):
            return f"Error: Test file not found: {abs_path}"

        # Build PYTHONPATH: tests/ first, then cloned_project/ so that
        # installed packages (like pytest) are found before cloned source,
        # but project modules are still importable.
        env = os.environ.copy()
        python_path_parts = [TEST_OUTPUT_DIR]
        if os.path.isdir(CLONED_PROJECT_DIR):
            # Also check for src/ layout (e.g. cloned_project/src/)
            src_dir = os.path.join(CLONED_PROJECT_DIR, "src")
            if os.path.isdir(src_dir):
                python_path_parts.append(src_dir)
            python_path_parts.append(CLONED_PROJECT_DIR)
        env["PYTHONPATH"] = os.pathsep.join(python_path_parts)

        result = subprocess.run(
            [sys.executable, "-m", "pytest", abs_path, "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=TEST_OUTPUT_DIR,
            env=env,
        )

        output_parts = []
        if result.stdout:
            output_parts.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"STDERR:\n{result.stderr}")
        output_parts.append(f"EXIT CODE: {result.returncode}")

        if result.returncode == 0:
            output_parts.insert(0, "ALL TESTS PASSED")
        else:
            output_parts.insert(0, "SOME TESTS FAILED")

        return "\n\n".join(output_parts)
    except subprocess.TimeoutExpired:
        return "Error: Test execution timed out after 120 seconds."
    except Exception as e:
        return f"Error running tests: {e}"


def check_syntax(file_path: str) -> str:
    """Check Python file syntax using py_compile.

    Args:
        file_path: Path to the Python file to check.

    Returns:
        Success message or syntax error details.
    """
    try:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return f"Error: File not found: {abs_path}"

        py_compile.compile(abs_path, doraise=True)
        return f"Syntax OK: {abs_path}"
    except py_compile.PyCompileError as e:
        return f"Syntax Error: {e}"
    except Exception as e:
        return f"Error checking syntax: {e}"
