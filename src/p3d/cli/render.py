"""p3d render — render control commands."""

from __future__ import annotations

import click

from p3d.cli._util import require_project, require_runtime


@click.group()
def render():
    """Render control."""
    pass


@render.command("frame")
@click.option("--count", default=1, help="Number of frames to render.")
def render_frame(count: int):
    """Render N frames (useful in offscreen/headless mode)."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("render.frame", {"count": count})
    click.echo(f"Rendered {result['rendered']} frame(s).")


@render.command("set")
@click.argument("prop")
@click.argument("val")
def render_set(prop: str, val: str):
    """Set a render property (bg-color, wireframe, fps-meter)."""
    pm = require_project()
    client = require_runtime(pm)
    if val.lower() in ("true", "on", "1"):
        parsed_val = True
    elif val.lower() in ("false", "off", "0"):
        parsed_val = False
    elif "," in val:
        parsed_val = [float(x.strip()) for x in val.split(",")]
    else:
        parsed_val = val
    client.call("render.set", {"prop": prop, "val": parsed_val})
    click.echo(f"Set {prop} = {parsed_val}")
