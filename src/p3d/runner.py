"""Game runner — launched as subprocess by `p3d run`."""

from __future__ import annotations

import argparse
import atexit
import importlib.util
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--window-type", default="onscreen", choices=["onscreen", "offscreen", "none"])
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    os.chdir(project_dir)

    from panda3d.core import loadPrcFileData

    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

    from p3d.core import ProjectManager
    pm = ProjectManager(project_dir)
    loadPrcFileData("p3d-project", pm.to_prc())
    loadPrcFileData("p3d-window", f"window-type {args.window_type}")
    pm.pid_file.write_text(str(os.getpid()))

    from direct.showbase.ShowBase import ShowBase

    base = _load_game_class(project_dir) or ShowBase()

    from p3d.core.runtime_server import ControlServer
    from p3d.core.rpc_methods import register_all

    server = ControlServer(pm.sock_path, base)
    register_all(server, base)
    server.start()

    default_scene = pm.get_default_scene()
    if default_scene and default_scene.exists():
        from p3d.core.scene_builder import load_scene_yaml, build_scene
        build_scene(load_scene_yaml(default_scene), base)

    atexit.register(lambda: (server.stop(), pm.pid_file.unlink(missing_ok=True)))
    base.run()


def _load_game_class(project_dir: Path):
    main_py = project_dir / "main.py"
    if not main_py.exists():
        return None
    from direct.showbase.ShowBase import ShowBase
    spec = importlib.util.spec_from_file_location("game_main", main_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in dir(mod):
        attr = getattr(mod, name)
        if isinstance(attr, type) and issubclass(attr, ShowBase) and attr is not ShowBase:
            return attr()
    return None


if __name__ == "__main__":
    main()
