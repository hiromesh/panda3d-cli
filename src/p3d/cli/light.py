"""p3d light — light management commands."""

from __future__ import annotations

import click

from p3d.cli._util import require_project, require_runtime, parse_vec


@click.group()
def light():
    """Manage scene lights."""
    pass


@light.command("add")
@click.argument("light_type", type=click.Choice(["ambient", "directional", "point", "spot"]))
@click.option("--name", default="light", help="Light name.")
@click.option("--color", default="1,1,1,1", help="Color r,g,b,a")
@click.option("--pos", default=None, help="Position x,y,z (point/spot)")
@click.option("--direction", default=None, help="Direction h,p,r (directional/spot)")
def light_add(light_type: str, name: str, color: str, pos, direction):
    """Add a light to the scene."""
    pm = require_project()
    client = require_runtime(pm)
    params: dict = {"type": light_type, "name": name, "color": parse_vec(color)}
    if pos:
        params["pos"] = parse_vec(pos)
    if direction:
        params["direction"] = parse_vec(direction)
    result = client.call("light.add", params)
    click.echo(f"Added light: {result['name']}")


@light.command("ls")
def light_ls():
    """List all lights."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("light.ls")
    for l in result.get("lights", []):
        click.echo(f"  {l['name']}  type={l['type']}  color={l['color']}")


@light.command("rm")
@click.argument("name")
def light_rm(name: str):
    """Remove a light by name."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("light.rm", {"name": name})
    click.echo(f"Removed: {result['removed']}")


@light.command("set")
@click.argument("name")
@click.option("--color", default=None, help="Color r,g,b,a")
@click.option("--pos", default=None, help="Position x,y,z")
@click.option("--direction", default=None, help="Direction h,p,r")
def light_set(name: str, color, pos, direction):
    """Modify a light's properties."""
    pm = require_project()
    client = require_runtime(pm)
    params: dict = {"name": name}
    if color:
        params["color"] = parse_vec(color)
    if pos:
        params["pos"] = parse_vec(pos)
    if direction:
        params["direction"] = parse_vec(direction)
    result = client.call("light.set", params)
    click.echo(f"Updated: {name}")
