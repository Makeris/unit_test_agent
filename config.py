"""Configuration for the test generator agent."""

import os

# OpenAI model configuration
MODEL_NAME = os.getenv("TEST_GEN_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Project paths — relative to test_gen_agent/ root
_AGENT_ROOT = os.path.dirname(os.path.abspath(__file__))
CLONED_PROJECT_DIR = os.path.join(_AGENT_ROOT, "cloned_project")
TEST_OUTPUT_DIR = os.path.join(_AGENT_ROOT, "tests")

# Agent settings
MAX_TOOL_ITERATIONS = 15
MAX_FIX_RETRIES = 3

# File size thresholds
LARGE_FILE_LINE_THRESHOLD = 1000
