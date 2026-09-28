"""`stampkit` command line interface."""

from __future__ import annotations

import typer

from stampkit import __version__

app = typer.Typer(help="StampKit - rapid manufacturability evaluation for sheet metal parts.")


@app.command()
def version() -> None:
    """Print the StampKit version."""
    typer.echo(__version__)


@app.command()
def evaluate(
    step: str = typer.Argument(..., help="Path to the part STEP file"),
    thickness: float = typer.Option(..., "-t", "--thickness", help="Sheet thickness in mm"),
    material: str = typer.Option(..., "-m", "--material", help="Material name"),
    ruleset: str = typer.Option("default", "--ruleset", help="Named ruleset"),
    rules_dir: str | None = typer.Option(None, "--rules", help="Directory with custom YAML rules"),
    fmt: str = typer.Option("md", "--format", help="json | md"),
) -> None:
    """Evaluate a sheet metal part (requires a CAD kernel)."""
    from stampkit.api.dto import EvaluateRequest, LocalPathInput
    from stampkit.api.service import StampKitService
    from stampkit.report.json_io import to_json
    from stampkit.report.render import render_markdown
    from stampkit.rules.loader import load_yaml_dir
    from stampkit.rules.registry import default_registry

    if rules_dir:
        load_yaml_dir(rules_dir, registry=default_registry)
    request = EvaluateRequest(
        part=LocalPathInput(path=step),
        thickness_mm=thickness,
        material=material,
        ruleset=ruleset,
    )
    report = StampKitService().evaluate(request)
    typer.echo(to_json(report) if fmt == "json" else render_markdown(report))


@app.command()
def doctor() -> None:
    """Check the runtime environment (kernel availability, versions)."""
    typer.echo(f"stampkit {__version__}")
    try:
        from stampkit.backends import get_kernel

        get_kernel()
    except Exception as e:  # noqa: BLE001 - doctor reports, never crashes
        typer.echo(f"freecad kernel: UNAVAILABLE ({e})")
    else:
        typer.echo("freecad kernel: ok")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
