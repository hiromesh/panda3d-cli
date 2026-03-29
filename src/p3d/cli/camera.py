"""p3d camera — camera control commands."""

from __future__ import annotations

import click

from p3d.cli._util import require_project, require_runtime, parse_vec


@click.group()
def camera():
    """Control the camera."""
    pass


@camera.command("get")
def camera_get():
    """Get camera position, rotation, and lens info."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("camera.get")
    for key, val in result.items():
        click.echo(f"  {key}: {val}")


@camera.command("set")
@click.option("--pos", default=None, help="Position x,y,z")
@click.option("--hpr", default=None, help="Rotation h,p,r")
@click.option("--look-at", default=None, help="Look-at target x,y,z")
@click.option("--fov", default=None, type=float, help="Field of view")
def camera_set(pos, hpr, look_at, fov):
    """Set camera properties."""
    pm = require_project()
    client = require_runtime(pm)
    params: dict = {}
    if pos:
        params["pos"] = parse_vec(pos)
    if hpr:
        params["hpr"] = parse_vec(hpr)
    if look_at:
        params["look_at"] = parse_vec(look_at)
    if fov is not None:
        params["fov"] = fov
    result = client.call("camera.set", params)
    click.echo(f"Camera: pos={result['pos']} hpr={result['hpr']} fov={result['fov']}")
