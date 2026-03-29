"""p3d init — scaffold a new project."""

from __future__ import annotations

import os
from pathlib import Path

import click
import yaml


PROJECT_TEMPLATE = {
    "project": {"name": "", "version": "0.1.0"},
    "window": {"title": "", "size": [1280, 720], "fullscreen": False},
    "render": {"background_color": [0.1, 0.1, 0.1, 1.0], "fps_meter": False},
    "paths": {"models": "assets/models", "textures": "assets/textures", "sounds": "assets/sounds"},
    "scene": {"default": "scenes/main.scene.yaml"},
    "physics": {"engine": "none", "gravity": [0, 0, -9.81]},
}

DEFAULT_SCENE = {
    "scene": {
        "name": "main",
        "lights": [
            {"name": "ambient", "type": "ambient", "color": [0.4, 0.4, 0.4, 1.0]},
            {"name": "sun", "type": "directional", "color": [0.8, 0.8, 0.75, 1.0], "direction": [1, 1, -2]},
        ],
        "nodes": [],
        "camera": {"pos": [0, -20, 10], "look_at": [0, 0, 0], "fov": 60},
    }
}

GITIGNORE = """\
.p3d/
__pycache__/
*.pyc
*.bam
"""

MAIN_PY = '''\
"""Game entry point — used by `p3d run`."""

from direct.showbase.ShowBase import ShowBase


class Game(ShowBase):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    game = Game()
    game.run()
'''


@click.command("init")
@click.argument("name")
def init(name: str) -> None:
    """Create a new p3d project."""
    project_dir = Path(os.getcwd()) / name

    if project_dir.exists():
        click.echo(f"Error: directory '{name}' already exists.", err=True)
        raise SystemExit(1)

    # Create directory structure
    dirs = [
        "scenes",
        "scripts",
        "assets/models",
        "assets/textures",
        "assets/sounds",
        "assets/fonts",
        "assets/shaders",
        "envs",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # p3d.yaml
    config = dict(PROJECT_TEMPLATE)
    config["project"]["name"] = name
    config["window"]["title"] = name
    with open(project_dir / "p3d.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Default scene
    with open(project_dir / "scenes" / "main.scene.yaml", "w") as f:
        yaml.dump(DEFAULT_SCENE, f, default_flow_style=False, sort_keys=False)

    # main.py
    with open(project_dir / "main.py", "w") as f:
        f.write(MAIN_PY)

    # .gitignore
    with open(project_dir / ".gitignore", "w") as f:
        f.write(GITIGNORE)

    click.echo(f"Created project '{name}' at {project_dir}")
    click.echo(f"  cd {name}")
    click.echo(f"  p3d run")
