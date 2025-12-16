import typer

from pytest_llm_agent.agent import target as generate_tests_target

app = typer.Typer(add_completion=False, help="CLI tool for generating pytest tests using LLMs")


@app.command(help="Generate verbose tests with detailed explanations")
def verbose(
    target: str = typer.Argument(..., help="path[:Class[:method]] or path::function"),
    prompt: str | None = typer.Option(None, "--prompt", help="Extra instructions for test generation"),
):
    ...


@app.command(help="Generate unit tests for the specified target")
def target(
    target: str = typer.Argument(..., help="path[:Class[:method]] or path::function"),
    out: str | None = typer.Argument(
        None,
        help="Optional output file or folder for the generated tests",
    ),
    prompt: str | None = typer.Option(None, "--prompt", help="Extra instructions for test generation"),
):
    generate_tests_target(target=target, out=out, prompt=prompt)


@app.command(help="Fix test as it fails. Provide the failing test and the error message.")
def fix(
    target: str = typer.Argument(..., help="path to the failing test file"),
    error: str = typer.Argument(..., help="Error message from the test failure"),
    prompt: str | None = typer.Option(None, "--prompt", help="Extra instructions for test fixing")
):
    ...


def main():
    app()


if __name__ == "__main__":
    main()
