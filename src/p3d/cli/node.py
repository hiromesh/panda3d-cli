"""p3d node — scene graph node operations."""

from __future__ import annotations

import click

from p3d.cli._util import require_project, require_runtime, parse_vec


@click.group()
def node():
    """Inspect and manipulate scene graph nodes."""
    pass


@node.command("ls")
@click.option("--path", default="/render", help="Parent node path.")
def node_ls(path: str):
    """List children of a node."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("node.ls", {"path": path})
    for child in result.get("children", []):
        click.echo(f"  {child['name']}  ({child['type']})")


@node.command("tree")
@click.option("--path", default="/render", help="Root node path.")
@click.option("--depth", default=10, help="Max depth.")
def node_tree(path: str, depth: int):
    """Print scene graph tree."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("node.tree", {"path": path, "depth": depth})
    _print_tree(result.get("tree", {}), 0)


def _print_tree(node_data: dict, indent: int):
    prefix = "  " * indent
    name = node_data.get("name", "?")
    ntype = node_data.get("type", "")
    click.echo(f"{prefix}{name}  ({ntype})")
    for child in node_data.get("children", []):
        _print_tree(child, indent + 1)


@node.command("get")
@click.argument("path")
def node_get(path: str):
    """Get node properties."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("node.get", {"path": path})
    for key, val in result.items():
        click.echo(f"  {key}: {val}")


@node.command("set")
@click.argument("path")
@click.option("--pos", default=None, help="Position x,y,z")
@click.option("--hpr", default=None, help="Rotation h,p,r")
@click.option("--scale", default=None, help="Scale (single or x,y,z)")
@click.option("--color", default=None, help="Color r,g,b,a")
@click.option("--visible/--hidden", default=None, help="Visibility")
def node_set(path: str, pos, hpr, scale, color, visible):
    """Set node properties."""
    pm = require_project()
    client = require_runtime(pm)
    params: dict = {"path": path}
    if pos:
        params["pos"] = parse_vec(pos)
    if hpr:
        params["hpr"] = parse_vec(hpr)
    if scale:
        parts = parse_vec(scale)
        params["scale"] = parts[0] if len(parts) == 1 else parts
    if color:
        params["color"] = parse_vec(color)
    if visible is not None:
        params["visible"] = visible
    result = client.call("node.set", params)
    click.echo(f"Updated: pos={result['pos']} hpr={result['hpr']} scale={result['scale']}")


@node.command("add")
@click.argument("parent_path", default="/render")
@click.option("--model", default=None, help="Model file to load.")
@click.option("--name", default="new_node", help="Node name.")
@click.option("--type", "node_type", default="model", help="Node type (model/actor/group).")
@click.option("--pos", default=None, help="Position x,y,z")
def node_add(parent_path: str, model, name, node_type, pos):
    """Add a node to the scene graph."""
    pm = require_project()
    client = require_runtime(pm)
    params: dict = {"parent": parent_path, "name": name, "type": node_type}
    if model:
        params["model"] = model
    if pos:
        params["pos"] = parse_vec(pos)
    result = client.call("node.add", params)
    click.echo(f"Added: {result['name']} at {result['pos']}")


@node.command("rm")
@click.argument("path")
def node_rm(path: str):
    """Remove a node from the scene graph."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("node.rm", {"path": path})
    click.echo(f"Removed: {result['removed']}")


@node.command("find")
@click.argument("pattern")
def node_find(pattern: str):
    """Find nodes by name pattern."""
    pm = require_project()
    client = require_runtime(pm)
    result = client.call("node.find", {"pattern": pattern})
    click.echo(f"Found {result['count']} node(s):")
    for n in result.get("matches", []):
        click.echo(f"  {n['path']}  pos={n['pos']}")
