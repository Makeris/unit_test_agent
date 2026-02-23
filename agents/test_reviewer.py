"""Test validation/review agent using AutoGen 0.4+ AssistantAgent."""

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config import MODEL_NAME
from prompts.system_prompts import TEST_REVIEWER_SYSTEM_PROMPT
from tools.test_runner import run_tests, check_syntax


def create_test_reviewer_agent() -> AssistantAgent:
    """Create and return the test reviewer AssistantAgent."""
    model_client = OpenAIChatCompletionClient(model=MODEL_NAME)

    agent = AssistantAgent(
        name="test_reviewer",
        model_client=model_client,
        tools=[run_tests, check_syntax],
        system_message=TEST_REVIEWER_SYSTEM_PROMPT,
        reflect_on_tool_use=True,
        max_tool_iterations=5,
    )
    return agent


async def review_tests(test_file_path: str) -> str:
    """Review and validate a generated test file.

    Args:
        test_file_path: Path to the test file to review.

    Returns:
        Review summary with pass/fail analysis.
    """
    task = (
        f"Review the test file at: {test_file_path}\n"
        f"Run the tests, check for syntax errors, and provide a detailed "
        f"analysis of the results including any failures and suggested fixes."
    )

    agent = create_test_reviewer_agent()
    await Console(agent.run_stream(task=task), output_stats=True)

    result = await agent.run(task="Provide the final review summary.")
    messages = result.messages
    if messages:
        return messages[-1].content
    return "Review completed."
