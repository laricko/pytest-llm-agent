# pytest-llm-agent

CLI helper to work with unit tests for your codebase.

## Installation

Install from PyPI with pip:

```bash
pip install pytest-llm-agent
```

## Configuration

You can choose model and add general default prompt

```toml
[tool.pytest-llm-agent]
model = "gpt-5"
# general_prompt = "Optional extra system prompt for the agent"
```

Secrets can be supplied through environment variables prefixed with `PYTEST_LLM_AGENT_`. For example, set `PYTEST_LLM_AGENT_API_KEY` in your shell and the agent will receive `API_KEY` in its environment at runtime.

```bash
EXPORT PYTEST_LLM_AGENT_API_KEY=foo
```

## Usage

After configuring your project, run the CLI to generate tests for a specific function, method, or class:

```bash
pytest-llm-agent target path/to/module.py:ClassName.method tests/test_module.py
```

You can optionally pass additional instructions to steer generation:

```bash
pytest-llm-agent target path/to/module.py::function tests/test_module.py --prompt "Focus on edge cases"
```

## Contribution

Very welcome. Make sure you also update tests if you add some services logic.

```
PYTHONPATH=. uv run pytest .
```