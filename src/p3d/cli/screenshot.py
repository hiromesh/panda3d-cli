"""p3d screenshot — capture a frame from the running game."""

from __future__ import annotations

from pathlib import Path

import click

from p3d.cli._util import require_project, require_runtime


@click.command()
@click.argument("output", default="screenshot.png")
def screenshot(output: str) -> None:
    """Capture a screenshot from the running game."""
    pm = require_project()
    client = require_runtime(pm)

    out_path = Path(output)
    if not out_path.is_absolute():
        out_path = pm.project_dir / out_path

    result = client.call("screenshot", {"output": str(out_path)})
    if result.get("ok"):
        click.echo(f"Screenshot saved: {result.get('path', out_path)}")
    else:
        click.echo(f"Error: {result.get('error', 'unknown')}", err=True)
        raise SystemExit(1)
