from dotenv import load_dotenv

load_dotenv()

import os
import asyncio
import subprocess

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


def run_tests(file_path="test_main.py"):
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", file_path], capture_output=True, text=True
        )
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return str(e)


def chunk_code(source_code: str, max_lines: int = 200):
    lines = source_code.splitlines()
    for i in range(0, len(lines), max_lines):
        yield "\n".join(lines[i : i + max_lines])


def write_code_to_file(prepared_code: str):
    with open("test_main.py", "w", encoding="utf-8") as f:
        f.write(prepared_code)


async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"], temperature=0.2
    )

    assistant = AssistantAgent(
        "assistant",
        tools=[write_code_to_file],
        description="Agent that generates unit tests for provided code",
        model_client=model_client,
        system_message="""
        Generate pytest tests in class format for given code.
        - Remove explanations and markers.
        - Use unittest.mock for external dependencies.
        - Provide meaningful sample data.
        - If the file is a controller, include request/response samples.
        - If the file is a service, test business logic with mocks.
        - If the file is a repository, mock database interactions.
        - Don't import external dependency.
        """,
    )

    team = RoundRobinGroupChat([assistant], max_turns=5)

    # source_code = """ import requests def fetch_data(url: str) -> dict: response = requests.get(url) response.raise_for_status() return response.json() """
    source_code = """ import sqlite3 def get_user_by_id(user_id: int) -> dict: conn = sqlite3.connect("users.db") cursor = conn.cursor() cursor.execute("SELECT id, name FROM users WHERE id=?", (user_id,)) row = cursor.fetchone() conn.close() if row: return {"id": row[0], "name": row[1]} return None """
    source_code_time = """ import datetime def get_current_year() -> int: return datetime.datetime.now().year """  # Функція з логером
    source_code_logger = """ import logging logger = logging.getLogger(__name__) def process_item(item: str) -> str: logger.info("Processing item: %s", item) return item.upper() """

    test_file_content = ""
    for chunk in chunk_code(source_code_logger, max_lines=200):
        task = f"Generate pytest unit tests for this code:\n{chunk}, prepare it and write it to file clear without any markers and other unneeded elements. Write for required methods internal implementation inside file"
        stream = team.run_stream(task=task)
        await Console(stream)

        result = await assistant.run(task=task)
        if result.messages:
            response_text = result.messages[-1].content
        else:
            response_text = str(result)

        test_file_content += "\n" + response_text

    while True:
        feedback = run_tests("test_main.py")
        print(feedback)

        task = input("Enter feedback for agent (or type 'exit'): ")
        if task.lower().strip() == "exit":
            break

        fix_task = f"Fix the unit tests based on this pytest output:\n{feedback}\nUser feedback: {task}"

        result = await assistant.run(task=fix_task)

        if result.messages:
            response_text = result.messages[-1].content
        else:
            response_text = str(result)

        print(response_text)
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
