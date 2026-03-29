"""p3d config — runtime configuration commands."""

from __future__ import annotations

import click

from p3d.cli._util import require_project, require_runtime


@click.group()
def config():
    """Get/set runtime configuration."""
    pass


@config.command("get")
@click.argument("key", required=False, default=None)
def config_get(key: str | None):
    """Get a config value (or list all)."""
    pm = require_project()
    client = require_runtime(pm)
    params = {"key": key} if key else {}
    result = client.call("config.get", params)
    if key:
        click.echo(f"{result['key']} = {result['value']}")
    else:
        for k, v in result.get("config", {}).items():
            click.echo(f"  {k} = {v}")
        click.echo(f"({result.get('total', '?')} total)")


@config.command("set")
@click.argument("key")
@click.argument("val")
def config_set(key: str, val: str):
    """Set a runtime config value."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("config.set", {"key": key, "val": val})
    click.echo(f"Set: {result['key']} = {result['val']}")
