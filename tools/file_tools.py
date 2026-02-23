"""File operation tools for the test generator agent."""

import glob
import os
import shutil
import subprocess

from config import CLONED_PROJECT_DIR, TEST_OUTPUT_DIR


def clone_repository(repo_url: str) -> str:
    """Clone a git repository into the cloned_project/ folder inside the agent project.

    The cloned_project/ folder is cleared before cloning so it always
    contains exactly the target repository.

    Args:
        repo_url: The URL of the git repository to clone.

    Returns:
        The path to the cloned repository, or an error message.
    """
    try:
        if os.path.exists(CLONED_PROJECT_DIR):
            shutil.rmtree(CLONED_PROJECT_DIR)
        result = subprocess.run(
            ["git", "clone", repo_url, CLONED_PROJECT_DIR],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return f"Error cloning repository: {result.stderr}"
        return f"Successfully cloned repository to: {CLONED_PROJECT_DIR}"
    except Exception as e:
        return f"Error cloning repository: {e}"


def install_dependencies(directory: str = "") -> str:
    """Install Python dependencies for a cloned project.

    Looks for requirements.txt, setup.py, setup.cfg, or pyproject.toml
    in the given directory (defaults to cloned_project/) and installs
    dependencies via pip.

    Args:
        directory: Path to the project root. Defaults to cloned_project/.

    Returns:
        Installation output or an error message.
    """
    import sys

    project_dir = directory if directory else CLONED_PROJECT_DIR
    if not os.path.isdir(project_dir):
        return f"Error: Directory not found: {project_dir}"

    try:
        # Try requirements.txt first — filter out protected packages
        req_file = os.path.join(project_dir, "requirements.txt")
        if os.path.isfile(req_file):
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file],
                capture_output=True, text=True, timeout=300,
            )
            return f"pip install -r requirements.txt\n\n{result.stdout}\n{result.stderr}".strip()

        # Try pyproject.toml / setup.py / setup.cfg
        # Use --no-deps to only install the package itself without pulling
        # in dependencies that could overwrite critical packages (e.g. pytest)
        for marker in ("pyproject.toml", "setup.py", "setup.cfg"):
            if os.path.isfile(os.path.join(project_dir, marker)):
                # First install deps from requires (but not the package itself as editable)
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", project_dir],
                    capture_output=True, text=True, timeout=300,
                )
                output = f"pip install {project_dir}\n\n{result.stdout}\n{result.stderr}".strip()

                # Re-install protected packages to undo any overwrites
                protected = ["pytest", "autogen-agentchat", "autogen-ext", "autogen-core"]
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--force-reinstall"] + protected,
                    capture_output=True, text=True, timeout=120,
                )
                return output + "\n\n(Re-installed protected packages: " + ", ".join(protected) + ")"

        return "No requirements.txt, pyproject.toml, setup.py, or setup.cfg found."
    except subprocess.TimeoutExpired:
        return "Error: pip install timed out after 5 minutes."
    except Exception as e:
        return f"Error installing dependencies: {e}"


def read_source_file(file_path: str) -> str:
    """Read and return the contents of a source file.

    Args:
        file_path: Absolute or relative path to the source file.

    Returns:
        The file contents as a string, or an error message.
    """
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        line_count = content.count("\n") + 1
        return f"# File: {abs_path} ({line_count} lines)\n\n{content}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_test_file(file_path: str, content: str) -> str:
    """Write generated test content to a file.

    If file_path is just a filename (e.g. "test_add.py"), it is placed
    inside the tests/ folder of the agent project automatically.

    Args:
        file_path: Path (or filename) where the test file should be written.
        content: The test file content to write.

    Returns:
        A success or error message.
    """
    try:
        if os.path.basename(file_path) == file_path:
            abs_path = os.path.join(TEST_OUTPUT_DIR, file_path)
        else:
            abs_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote test file: {abs_path}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_project_files(directory: str, pattern: str = "**/*.py") -> str:
    """List project files matching a glob pattern.

    Args:
        directory: Root directory to search from.
        pattern: Glob pattern to match files (default: all Python files).

    Returns:
        Newline-separated list of matching file paths.
    """
    try:
        abs_dir = os.path.abspath(directory)
        matches = glob.glob(os.path.join(abs_dir, pattern), recursive=True)
        if not matches:
            return f"No files matching '{pattern}' found in {abs_dir}"
        matches.sort()
        return "\n".join(matches)
    except Exception as e:
        return f"Error listing files: {e}"
