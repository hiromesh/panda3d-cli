"""ProjectManager — reads p3d.yaml, resolves paths, generates PRC config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = {
    "project": {"name": "untitled", "version": "0.1.0"},
    "window": {"title": "Panda3D Game", "size": [1280, 720], "fullscreen": False},
    "render": {"background_color": [0.1, 0.1, 0.1, 1.0], "fps_meter": False},
    "paths": {"models": "assets/models", "textures": "assets/textures", "sounds": "assets/sounds"},
    "scene": {"default": None},
    "physics": {"engine": "none", "gravity": [0, 0, -9.81]},
}


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


class ProjectManager:
    """Manages a p3d project: config, paths, PRC generation."""

    CONFIG_FILE = "p3d.yaml"
    RUNTIME_DIR = ".p3d"
    PID_FILE = "runtime.pid"
    SOCK_FILE = "runtime.sock"

    def __init__(self, project_dir: str | Path | None = None):
        self.project_dir = Path(project_dir or os.getcwd()).resolve()
        self.config: dict[str, Any] = {}
        _deep_merge(self.config, DEFAULT_CONFIG)
        config_path = self.project_dir / self.CONFIG_FILE
        if config_path.exists():
            with open(config_path) as f:
                user_config = yaml.safe_load(f) or {}
            _deep_merge(self.config, user_config)

    @property
    def runtime_dir(self) -> Path:
        d = self.project_dir / self.RUNTIME_DIR
        d.mkdir(exist_ok=True)
        return d

    @property
    def pid_file(self) -> Path:
        return self.runtime_dir / self.PID_FILE

    @property
    def sock_path(self) -> Path:
        return self.runtime_dir / self.SOCK_FILE

    @property
    def name(self) -> str:
        return self.config["project"]["name"]

    def to_prc(self) -> str:
        """Generate PRC config string from p3d.yaml settings."""
        lines: list[str] = []
        win = self.config.get("window", {})
        lines.append(f"window-title {win.get('title', 'Panda3D Game')}")
        size = win.get("size", [1280, 720])
        lines.append(f"win-size {size[0]} {size[1]}")
        if win.get("fullscreen"):
            lines.append("fullscreen #t")

        render_cfg = self.config.get("render", {})
        bg = render_cfg.get("background_color", [0.1, 0.1, 0.1, 1.0])
        lines.append(f"background-color {bg[0]} {bg[1]} {bg[2]} {bg[3]}")
        if render_cfg.get("fps_meter"):
            lines.append("show-frame-rate-meter #t")

        paths = self.config.get("paths", {})
        for path_type in ("models", "textures", "sounds"):
            p = paths.get(path_type)
            if p:
                abs_path = self.project_dir / p
                lines.append(f"model-path {abs_path}")

        return "\n".join(lines)

    def is_project(self) -> bool:
        return (self.project_dir / self.CONFIG_FILE).exists()

    def get_default_scene(self) -> Path | None:
        scene = self.config.get("scene", {}).get("default")
        if scene:
            return self.project_dir / scene
        return None

    def resolve(self, relative_path: str) -> Path:
        return self.project_dir / relative_path
