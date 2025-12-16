import os
from typing import Any, Protocol

from langchain.agents import create_agent

from pytest_llm_agent.config import PytestLLMAgentConfig
from pytest_llm_agent.core.services import PytestAgentToolsService
from pytest_llm_agent.repository import SqliteUnitTestDbRepository
from pytest_llm_agent.tools import build_langchain_tools

db_repository = SqliteUnitTestDbRepository()
service = PytestAgentToolsService(unit_test_repo=db_repository)
tools = build_langchain_tools(service)


class AgentInvoker(Protocol):
    def invoke(self, input: Any, *args: Any, **kwargs: Any) -> Any: ...


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

llm_config = PytestLLMAgentConfig.load()
for key, value in llm_config.secrets.items():
    os.environ[key] = value

agent: AgentInvoker = create_agent(
    llm_config.model,
    tools=tools,
    system_prompt=llm_config.general_prompt or DEFAULT_SYSTEM_PROMPT,
)


def target(target: str, out: str | None = None, prompt: str | None = None):
    output_instruction = f"Write the tests to: {out}. " if out else ""

    agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate pytest unit tests for the target: {target}. "
                    f"{output_instruction}" + (f"Additional instructions: {prompt}" if prompt else ""),
                }
            ]
        }
    )
