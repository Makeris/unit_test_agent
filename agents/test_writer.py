"""Core test-writing agent using AutoGen 0.4+ AssistantAgent."""

import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config import MODEL_NAME, TEST_OUTPUT_DIR, MAX_TOOL_ITERATIONS
from prompts.system_prompts import TEST_WRITER_SYSTEM_PROMPT
from tools.file_tools import clone_repository, install_dependencies, read_source_file, write_test_file, list_project_files
from tools.test_runner import run_tests, check_syntax
from tools.code_analyzer import (
    analyze_dependencies,
    detect_file_type,
    analyze_file_structure,
    read_file_section,
)


def _build_test_path(source_path: str) -> str:
    """Derive the test file output path from the source file path."""
    abs_source = os.path.abspath(source_path)
    basename = os.path.basename(abs_source)
    name, ext = os.path.splitext(basename)
    test_filename = f"test_{name}{ext}"
    output_dir = os.path.abspath(TEST_OUTPUT_DIR)
    return os.path.join(output_dir, test_filename)


def create_test_writer_agent() -> AssistantAgent:
    """Create and return the test writer AssistantAgent with all tools."""
    model_client = OpenAIChatCompletionClient(model=MODEL_NAME)

    agent = AssistantAgent(
        name="test_writer",
        model_client=model_client,
        tools=[
            clone_repository,
            install_dependencies,
            read_source_file,
            write_test_file,
            list_project_files,
            run_tests,
            check_syntax,
            analyze_dependencies,
            detect_file_type,
            analyze_file_structure,
            read_file_section,
        ],
        system_message=TEST_WRITER_SYSTEM_PROMPT,
        reflect_on_tool_use=True,
        max_tool_iterations=MAX_TOOL_ITERATIONS,
    )
    return agent


async def generate_tests_for_repo(repo_url: str) -> str:
    """Clone a repository and generate tests for all Python source files.

    Args:
        repo_url: URL of the git repository.

    Returns:
        Summary of the generation results.
    """
    task = (
        f"Generate pytest unit tests for the repository at: {repo_url}\n\n"
        f"Follow these steps:\n"
        f"1. Clone the repository using clone_repository('{repo_url}')\n"
        f"2. List all Python files using list_project_files() on the cloned directory\n"
        f"3. For each Python source file (skip __init__.py, setup.py, test files, and config files):\n"
        f"   a. Analyze the file type and dependencies\n"
        f"   b. Read the source code\n"
        f"   c. Generate pytest tests\n"
        f"   d. Write the test file into a tests/generated/ directory inside the cloned repo\n"
        f"   e. Check syntax and run the tests\n"
        f"   f. Fix any failures (up to 3 retries per file)\n"
        f"4. Provide a final summary of all generated test files and their results."
    )

    agent = create_test_writer_agent()
    await Console(agent.run_stream(task=task), output_stats=True)

    result = await agent.run(task="Provide a final summary of all generated test files and results.")
    messages = result.messages
    if messages:
        return messages[-1].content
    return "Repository test generation completed."


async def generate_tests(source_path: str) -> str:
    """Generate tests for a source file.

    Args:
        source_path: Path to the Python source file to test.

    Returns:
        Summary of the generation results.
    """
    abs_source = os.path.abspath(source_path)
    test_path = _build_test_path(source_path)

    task = (
        f"Generate pytest unit tests for the following source file:\n"
        f"  Source file: {abs_source}\n"
        f"  Write the test file to: {test_path}\n\n"
        f"Follow your workflow: analyze the file type, analyze dependencies, "
        f"read the source, generate tests, write them, check syntax, and run them. "
        f"If tests fail, fix and retry up to 3 times."
    )

    agent = create_test_writer_agent()

    await Console(agent.run_stream(task=task), output_stats=True)

    # Extract the final message as the summary
    result = await agent.run(task="Provide a final summary of what was generated and the test results.")
    messages = result.messages
    if messages:
        return messages[-1].content
    return "Test generation completed."
