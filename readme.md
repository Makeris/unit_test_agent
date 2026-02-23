# Test Generator Agent

This project provides a CLI entry point for a test generator agent that uses OpenAI's API to automatically create Python test files based on a given prompt.

## How it works
- The main entry point is `main.py`.
- It loads environment variables from a `.env` file.
- It requires an `OPENAI_API_KEY` to interact with the OpenAI API.
- The agent generates test files in the `tests/` directory based on the prompt you define in `main.py`.
- Cloned project will be at own folder

## Local Setup

1. Clone or download the repository.
2. Install required dependency (for example from `requirements.txt`).
3. Create a `.env` file in the project root with your OpenAI API key:
4. Run "main.py" file.
