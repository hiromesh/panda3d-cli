"""p3d run / stop / status — game lifecycle commands."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import click

from p3d.cli._util import require_project
from p3d.core.runtime_client import RuntimeClient


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _get_running_pid(pm) -> int | None:
    if not pm.pid_file.exists():
        return None
    try:
        pid = int(pm.pid_file.read_text().strip())
    except (ValueError, OSError):
        return None
    if _pid_alive(pid):
        return pid
    pm.pid_file.unlink(missing_ok=True)
    return None


@click.command()
@click.option("--headless", is_flag=True, help="No window, no GPU.")
@click.option("--offscreen", is_flag=True, help="GPU rendering, no window.")
def run(headless: bool, offscreen: bool) -> None:
    """Start the game."""
    pm = require_project()

    if _get_running_pid(pm):
        click.echo("Game is already running. Use `p3d stop` first.", err=True)
        raise SystemExit(1)

    window_type = "none" if headless else ("offscreen" if offscreen else "onscreen")

    if pm.sock_path.exists():
        pm.sock_path.unlink()

    cmd = [sys.executable, "-m", "p3d.runner",
           "--project-dir", str(pm.project_dir),
           "--window-type", window_type]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL if headless else None,
        stderr=subprocess.DEVNULL if headless else None,
    )

    client = RuntimeClient(pm.sock_path)
    deadline = time.time() + 10.0
    while time.time() < deadline:
        if client.is_connected():
            click.echo(f"Game started (PID {proc.pid}, {window_type} mode).")
            return
        time.sleep(0.2)
        if proc.poll() is not None:
            click.echo(f"Error: game process exited with code {proc.returncode}.", err=True)
            raise SystemExit(1)

    click.echo(f"Warning: started but control server not responding. PID: {proc.pid}", err=True)


@click.command()
def stop() -> None:
    """Stop the running game."""
    pm = require_project()
    pid = _get_running_pid(pm)
    if not pid:
        click.echo("No game is running.")
        return

    client = RuntimeClient(pm.sock_path)
    try:
        client.shutdown()
        deadline = time.time() + 5.0
        while time.time() < deadline and _pid_alive(pid):
            time.sleep(0.2)
        if not _pid_alive(pid):
            click.echo("Game stopped.")
            pm.pid_file.unlink(missing_ok=True)
            return
    except Exception:
        pass

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
        if _pid_alive(pid):
            os.kill(pid, signal.SIGKILL)
    except OSError:
        pass

    pm.pid_file.unlink(missing_ok=True)
    pm.sock_path.unlink(missing_ok=True)
    click.echo("Game stopped (forced).")


@click.command()
def status() -> None:
    """Show game runtime status."""
    pm = require_project()
    pid = _get_running_pid(pm)
    if not pid:
        click.echo("Status: not running")
        return

    client = RuntimeClient(pm.sock_path)
    try:
        info = client.status()
        click.echo(f"Status: running")
        click.echo(f"  PID:        {info.get('pid', pid)}")
        click.echo(f"  FPS:        {info.get('fps', '?')}")
        click.echo(f"  Nodes:      {info.get('node_count', '?')}")
    except Exception:
        click.echo(f"Status: running (PID {pid}, control server unreachable)")
