"""p3d script — behavior script management."""

from __future__ import annotations

import click

from p3d.cli._util import require_project, require_runtime


@click.group()
def script():
    """Manage behavior scripts attached to nodes."""
    pass


@script.command("attach")
@click.argument("node_path")
@click.argument("script_file")
def script_attach(node_path: str, script_file: str):
    """Attach a behavior script to a node."""
    pm = require_project()
    client = require_runtime(pm)
    path = pm.resolve(script_file)
    result = client.call("script.attach", {"path": node_path, "script": str(path)})
    click.echo(f"Attached {result['script']} to {result['node']}")


@script.command("detach")
@click.argument("node_path")
@click.argument("script_file")
def script_detach(node_path: str, script_file: str):
    """Detach a behavior script from a node."""
    pm = require_project()
    client = require_runtime(pm)
    path = pm.resolve(script_file)
    result = client.call("script.detach", {"path": node_path, "script": str(path)})
    click.echo("Detached.")


@script.command("list")
@click.option("--path", default="/render", help="Node path.")
def script_list(path: str):
    """List scripts attached to a node."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("script.list", {"path": path})
    scripts = result.get("scripts", [])
    if not scripts:
        click.echo("No scripts attached.")
        return
    for s in scripts:
        click.echo(f"  {s['class']}  ({s['path']})")


@script.command("run")
@click.argument("script_file")
def script_run(script_file: str):
    """Execute a Python script in the running game context."""
    pm = require_project()
    client = require_runtime(pm)
    path = pm.resolve(script_file)
    result = client.call("script.run", {"script": str(path)})
    click.echo(f"Executed: {result['script']}")
