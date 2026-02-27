"""CLI entry point for the test generator agent."""

import asyncio
import os
import sys

# Add the project root to sys.path so imports work when run from any directory
_project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_dir)

from dotenv import load_dotenv
load_dotenv()

from autogen_agentchat.ui import Console
from agents.test_writer import create_test_writer_agent
from config import TEST_OUTPUT_DIR

# ====================================================================
# YOUR PROMPT — edit this variable and run: python main.py
# ====================================================================
PROMPT = "Write me tests for this repository def factorial(n): if n == 0 or n == 1: return 1 return n * factorial(n - 1)"
# PROMPT = "Write me tests for this repository https://github.com/nedbat/pkgsample"
# PROMPT = "Write me tests for this repository https://github.com/TheAlgorithms/Python"
# ====================================================================


def _ensure_tests_dir():
    """Create the tests/ output directory if it doesn't exist."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)


def _list_test_files():
    """Return list of .py test files in tests/ directory."""
    if not os.path.isdir(TEST_OUTPUT_DIR):
        return []
    return [f for f in os.listdir(TEST_OUTPUT_DIR) if f.startswith("test_") and f.endswith(".py")]


async def async_main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Check your .env file.", file=sys.stderr)
        sys.exit(1)

    prompt = PROMPT.strip()
    if not prompt:
        print("Error: PROMPT is empty. Edit main.py and write your request.", file=sys.stderr)
        sys.exit(1)

    _ensure_tests_dir()
    files_before = set(_list_test_files())

    print(f"Prompt:\n{prompt}")
    print("=" * 60)

    agent = create_test_writer_agent()
    await Console(agent.run_stream(task=prompt), output_stats=True)

    # Show what was generated
    files_after = set(_list_test_files())
    new_files = files_after - files_before
    if new_files:
        print("\n" + "=" * 60)
        print(f"Generated test files in {TEST_OUTPUT_DIR}:")
        for f in sorted(new_files):
            print(f"  - {f}")
    else:
        print("\n" + "=" * 60)
        print(f"WARNING: No new test files were created in {TEST_OUTPUT_DIR}")
        print("The agent may have output tests as text instead of saving them.")
        print("Try giving feedback below to ask the agent to save the tests.")

    # Feedback loop — ask user for follow-up instructions
    while True:
        print("\n" + "=" * 60)
        try:
            feedback = input("Your feedback (or 'exit' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not feedback or feedback.lower() in ("exit", "quit", "q"):
            print("Done.")
            break

        await Console(agent.run_stream(task=feedback), output_stats=True)

        files_now = set(_list_test_files())
        new_after_feedback = files_now - files_after
        if new_after_feedback:
            print(f"\nNew test files: {', '.join(sorted(new_after_feedback))}")
            files_after = files_now


if __name__ == "__main__":
    asyncio.run(async_main())
