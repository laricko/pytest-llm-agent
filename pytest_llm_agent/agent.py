from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from pytest_llm_agent.core.services import PytestAgentToolsService
from pytest_llm_agent.tools import build_langchain_tools

DEFAULT_SYSTEM_PROMPT = """\
You are a pytest unit-test generation agent.

Your job:
- Generate or update pytest tests for a given target function/method.
- You MUST interact with the repository only through the provided tools.
- You may read an existing test file for context before writing.
- When writing, ONLY modify the managed blocks created by PYTEST_LLM_AGENT markers.
- Keep tests deterministic: no network, no random, no real time (freeze time if needed).
- Prefer minimal dependencies: pytest + standard library.
- Use clear test names and assert meaningful behavior.

Workflow suggestion:
1) Read the current test file content (tool: test_file_read) if it exists.
2) Decide what to add/update.
3) Call test_create to create registry record + insert/update the managed block.
4) If updating existing test by id, use test_update_content.

Return a short summary of what you did at the end.
"""


@dataclass(frozen=True)
class AgentConfig:
    model: str = "gpt-5"
    temperature: float = 0.1
    max_tokens: int | None = None


def build_agent(
    service: PytestAgentToolsService,
    *,
    config: AgentConfig = AgentConfig(),
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> AgentExecutor:
    """
    Builds a LangChain tool-calling agent executor with your service-bound tools.
    """
    tools = build_langchain_tools(service)

    llm = ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=False,
        handle_parsing_errors=True,
    )


def run(
    executor: AgentExecutor,
    *,
    instruction: str,
    chat_history: Sequence[Any] | None = None,
) -> str:
    """
    Simple helper to run the agent with optional chat_history.
    """
    result = executor.invoke(
        {
            "input": instruction,
            "chat_history": list(chat_history or []),
        }
    )
    return str(result["output"])
