"""Shared CLI utilities."""

from __future__ import annotations

import click

from p3d.core import ProjectManager
from p3d.core.runtime_client import RuntimeClient


def require_project() -> ProjectManager:
    pm = ProjectManager()
    if not pm.is_project():
        click.echo("Error: not a p3d project (no p3d.yaml found).", err=True)
        raise SystemExit(1)
    return pm


def require_runtime(pm: ProjectManager) -> RuntimeClient:
    client = RuntimeClient(pm.sock_path)
    if not client.is_connected():
        click.echo("Error: no game is running. Start with `p3d run` first.", err=True)
        raise SystemExit(1)
    return client


def parse_vec(s: str) -> list[float]:
    """Parse 'x,y,z' string to list of floats."""
    return [float(x.strip()) for x in s.split(",")]
