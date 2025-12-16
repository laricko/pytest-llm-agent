import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ENV_SECRET_PREFIX = "PYTEST_LLM_AGENT_"


def _load_prefixed_env(prefix: str = ENV_SECRET_PREFIX) -> dict[str, str]:
    return {k.removeprefix(prefix): v for k, v in os.environ.items() if k.startswith(prefix)}


@dataclass(slots=True)
class PytestLLMAgentConfig:
    model: str
    general_prompt: str | None = None
    secrets: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> "PytestLLMAgentConfig":
        path = path or Path("pyproject.toml")

        with path.open("rb") as f:
            data = tomllib.load(f)

        tool_cfg = data.get("tool", {})
        cfg = tool_cfg.get("pytest-llm-agent", data.get("pytest-llm-agent", {}))

        return cls(
            model=cfg.get("model", "gpt-5"),
            general_prompt=cfg.get("general_prompt"),
            secrets=_load_prefixed_env(),
        )
