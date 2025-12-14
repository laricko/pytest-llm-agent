import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PytestLLMAgentConfig:
    protocols: list[str]
    services: list[str]
    tests_dir: str
    model: str
    general_prompt: str | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> "PytestLLMAgentConfig":
        path = path or Path("pyproject.toml")

        with path.open("rb") as f:
            data = tomllib.load(f)

        cfg = data.get("pytest-llm-agent", {})
        services = cfg.get("services")
        if not services:
            raise ValueError("No services defined in configuration")

        protocols = cfg.get("protocols")
        if not protocols:
            raise ValueError("No protocols defined in configuration")

        return cls(
            protocols=protocols,
            services=services,
            tests_dir=cfg.get("tests_dir", "tests"),
            model=cfg.get("model"),
            general_prompt=cfg.get("general_prompt"),
        )
