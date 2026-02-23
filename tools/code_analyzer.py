"""Code analysis tools for the test generator agent."""

import ast
import os
import re


def analyze_dependencies(file_path: str) -> str:
    """Parse imports from a Python file and resolve to project files.

    Analyzes the import statements to identify project-local dependencies
    and summarizes their public interface (classes, functions, signatures).

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        Structured summary of dependencies with their signatures.
    """
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        project_root = _find_project_root(abs_path)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        results = []
        for module_name in imports:
            resolved = _resolve_module_to_file(module_name, project_root)
            if resolved and os.path.exists(resolved):
                summary = _summarize_module(resolved)
                results.append(f"## {module_name} ({resolved})\n{summary}")

        if not results:
            return "No project-local dependencies found. Only standard library / third-party imports detected."

        return "# Dependencies Analysis\n\n" + "\n\n".join(results)
    except SyntaxError as e:
        return f"Syntax error in source file: {e}"
    except Exception as e:
        return f"Error analyzing dependencies: {e}"


def detect_file_type(file_path: str) -> str:
    """Classify a Python file as controller, service, or repository.

    Uses heuristics based on file name, decorators, and content patterns.

    Args:
        file_path: Path to the Python file to classify.

    Returns:
        Classification result with reasoning.
    """
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            source = f.read()

        basename = os.path.basename(abs_path).lower()
        reasons = []

        # Controller / View indicators
        controller_signals = 0
        if "views" in basename or "routes" in basename or "endpoints" in basename or "controller" in basename:
            controller_signals += 2
            reasons.append(f"filename '{basename}' suggests controller/view")
        if re.search(r"@(app\.(route|get|post|put|delete|patch)|require_http_methods|api_view)", source):
            controller_signals += 2
            reasons.append("has HTTP route decorators")
        if re.search(r"(request\.|Response\(|JsonResponse|jsonify|HTTPResponse|render\()", source):
            controller_signals += 1
            reasons.append("references HTTP request/response objects")

        # Repository / Model indicators
        repo_signals = 0
        if "models" in basename or "repository" in basename or "repo" in basename or "dal" in basename:
            repo_signals += 2
            reasons.append(f"filename '{basename}' suggests repository/model")
        if re.search(r"(models\.Model|db\.Model|Base\s*=\s*declarative_base|\.query\.|\.filter\(|\.objects\.)", source):
            repo_signals += 2
            reasons.append("contains ORM/model patterns")
        if re.search(r"(session\.add|session\.commit|\.save\(\)|\.delete\(\)|bulk_create|SELECT|INSERT)", source):
            repo_signals += 1
            reasons.append("contains database operation patterns")

        # Service indicators
        service_signals = 0
        if "service" in basename or "logic" in basename or "usecase" in basename or "handler" in basename:
            service_signals += 2
            reasons.append(f"filename '{basename}' suggests service/business logic")
        if controller_signals == 0 and repo_signals == 0:
            service_signals += 1
            reasons.append("no HTTP or DB patterns found, likely business logic")

        # Determine winner
        scores = {
            "controller": controller_signals,
            "service": service_signals,
            "repository": repo_signals,
        }
        file_type = max(scores, key=scores.get)

        return (
            f"File type: {file_type}\n"
            f"Confidence scores: {scores}\n"
            f"Reasoning:\n" + "\n".join(f"  - {r}" for r in reasons)
        )
    except Exception as e:
        return f"Error detecting file type: {e}"


def analyze_file_structure(file_path: str) -> str:
    """Extract structural overview of a Python file using AST.

    Returns all classes, methods, and standalone functions with line ranges,
    arguments, and docstrings. Used for chunking large files.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        Structured summary of the file's classes, methods, and functions.
    """
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        total_lines = source.count("\n") + 1
        items = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_info = _extract_class_info(node)
                items.append(class_info)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = _extract_function_info(node)
                items.append(func_info)

        output = f"# File Structure: {abs_path}\n"
        output += f"# Total lines: {total_lines}\n\n"

        if not items:
            output += "No classes or functions found at module level."
            return output

        for item in items:
            output += item + "\n\n"

        return output
    except SyntaxError as e:
        return f"Syntax error in file: {e}"
    except Exception as e:
        return f"Error analyzing file structure: {e}"


def read_file_section(file_path: str, start_line: int, end_line: int) -> str:
    """Read a specific line range from a file.

    Args:
        file_path: Path to the file.
        start_line: First line to read (1-indexed).
        end_line: Last line to read (1-indexed, inclusive).

    Returns:
        The specified section of the file with line numbers.
    """
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total = len(lines)
        start = max(1, start_line)
        end = min(total, end_line)

        selected = lines[start - 1 : end]
        numbered = [f"{i}: {line}" for i, line in enumerate(selected, start=start)]

        return (
            f"# {abs_path} lines {start}-{end} (of {total})\n\n"
            + "".join(numbered)
        )
    except Exception as e:
        return f"Error reading file section: {e}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_project_root(file_path: str) -> str:
    """Walk up from file_path looking for project root markers."""
    current = os.path.dirname(os.path.abspath(file_path))
    markers = {"setup.py", "setup.cfg", "pyproject.toml", "manage.py", "requirements.txt", ".git"}
    for _ in range(10):
        if any(os.path.exists(os.path.join(current, m)) for m in markers):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.dirname(os.path.abspath(file_path))


def _resolve_module_to_file(module_name: str, project_root: str) -> str | None:
    """Try to resolve a dotted module name to a .py file in the project."""
    parts = module_name.split(".")
    # Try as package/module.py
    candidate = os.path.join(project_root, *parts) + ".py"
    if os.path.exists(candidate):
        return candidate
    # Try as package/__init__.py
    candidate = os.path.join(project_root, *parts, "__init__.py")
    if os.path.exists(candidate):
        return candidate
    return None


def _summarize_module(file_path: str) -> str:
    """Return a brief summary of a module's public interface."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception:
        return "  (could not parse)"

    parts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig = _format_signature(item)
                    methods.append(f"    - {sig}")
            parts.append(f"  class {node.name}:")
            parts.extend(methods if methods else ["    (no methods)"])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = _format_signature(node)
            parts.append(f"  {sig}")

    return "\n".join(parts) if parts else "  (empty module)"


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Format a function/method signature."""
    args = []
    for arg in node.args.args:
        annotation = ""
        if arg.annotation:
            annotation = ": " + ast.unparse(arg.annotation)
        args.append(f"{arg.arg}{annotation}")

    returns = ""
    if node.returns:
        returns = " -> " + ast.unparse(node.returns)

    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    return f"{prefix}{node.name}({', '.join(args)}){returns}"


def _extract_class_info(node: ast.ClassDef) -> str:
    """Extract class info including methods with line ranges."""
    end_line = node.end_lineno or node.lineno
    parts = [f"## class {node.name} (lines {node.lineno}-{end_line})"]

    docstring = ast.get_docstring(node)
    if docstring:
        parts.append(f"   Docstring: {docstring.split(chr(10))[0]}")

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            item_end = item.end_lineno or item.lineno
            sig = _format_signature(item)
            parts.append(f"   - {sig}  (lines {item.lineno}-{item_end})")

    return "\n".join(parts)


def _extract_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Extract standalone function info."""
    end_line = node.end_lineno or node.lineno
    sig = _format_signature(node)
    parts = [f"## {sig} (lines {node.lineno}-{end_line})"]

    docstring = ast.get_docstring(node)
    if docstring:
        parts.append(f"   Docstring: {docstring.split(chr(10))[0]}")

    return "\n".join(parts)
