"""p3d scene — scene YAML management commands."""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from p3d.cli._util import require_project, require_runtime


@click.group()
def scene():
    """Manage scenes."""
    pass


@scene.command("list")
def scene_list():
    """List all scene files in the project."""
    pm = require_project()
    scenes_dir = pm.project_dir / "scenes"
    if not scenes_dir.exists():
        click.echo("No scenes/ directory.")
        return
    for f in sorted(scenes_dir.glob("*.scene.yaml")):
        click.echo(f"  {f.relative_to(pm.project_dir)}")


@scene.command("load")
@click.argument("file")
def scene_load(file: str):
    """Load a scene YAML into the running game."""
    pm = require_project()
    client = require_runtime(pm)
    path = pm.resolve(file)
    if not path.exists():
        click.echo(f"Error: {file} not found.", err=True)
        raise SystemExit(1)
    result = client.call("scene.load", {"path": str(path)})
    click.echo(f"Scene loaded: {result.get('scene', file)}")


@scene.command("save")
@click.argument("file")
def scene_save(file: str):
    """Export current scene graph to YAML."""
    pm = require_project()
    client = require_runtime(pm)
    path = pm.resolve(file)
    result = client.call("scene.save", {"path": str(path)})
    click.echo(f"Scene saved: {result.get('path', file)}")


@scene.command("validate")
@click.argument("file")
def scene_validate(file: str):
    """Validate a scene YAML file (offline, no runtime needed)."""
    pm = require_project()
    path = pm.resolve(file)
    if not path.exists():
        click.echo(f"Error: {file} not found.", err=True)
        raise SystemExit(1)
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if not data or "scene" not in data:
            click.echo(f"Error: missing top-level 'scene' key.", err=True)
            raise SystemExit(1)
        scene_data = data["scene"]
        required = ["name"]
        for key in required:
            if key not in scene_data:
                click.echo(f"Error: missing 'scene.{key}'.", err=True)
                raise SystemExit(1)
        click.echo(f"Valid: {file}")
    except yaml.YAMLError as e:
        click.echo(f"YAML error: {e}", err=True)
        raise SystemExit(1)
