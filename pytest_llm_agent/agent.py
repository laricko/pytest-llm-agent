from langchain.agents import create_agent

from pytest_llm_agent.core.services import PytestAgentToolsService
from pytest_llm_agent.repository import SqliteUnitTestDbRepository
from pytest_llm_agent.tools import build_langchain_tools

db_repository = SqliteUnitTestDbRepository()
service = PytestAgentToolsService(unit_test_repo=db_repository)
tools = build_langchain_tools(service)


DEFAULT_SYSTEM_PROMPT = """\
You are a pytest unit-test generation agent.

Your job:
- Generate or update pytest tests for a given target function/method.
- You may read an existing test file for context before writing.
- When writing, ONLY modify the managed blocks created by PYTEST_LLM_AGENT markers.
- Keep tests deterministic: no network, no random, no real time (freeze time if needed).
- Prefer minimal dependencies: pytest + standard library.
- Make sure you use unittest mock to mock dependencies, and check these mock calls after all.

Return a short summary of what you did at the end.
"""

agent = create_agent(
    "gpt-5",
    tools=tools,
    system_prompt=DEFAULT_SYSTEM_PROMPT,
)


def target(target: str, out: str, prompt: str | None = None):
    agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate pytest unit tests for the target: {target}. "
                    f"Write the tests to: {out}. "
                    + (f"Additional instructions: {prompt}" if prompt else ""),
                }
            ]
        }
    )
