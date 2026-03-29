"""RPC method handlers — all JSON-RPC methods the control server exposes."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable

from panda3d.core import Vec3, Vec4


_METHODS: dict[str, Callable] = {}


def rpc(name: str):
    def decorator(fn: Callable) -> Callable:
        _METHODS[name] = fn
        return fn
    return decorator


def register_all(server: Any, base: Any) -> None:
    for name, fn in _METHODS.items():
        server.register(name, lambda params, _fn=fn, _base=base: _fn(params, _base))


def _resolve_node(path: str, base: Any) -> Any:
    if path in ("/render", "render"):
        return base.render
    search = path
    if search.startswith("/render/"):
        search = search[len("/render/"):]
    elif search.startswith("/render"):
        return base.render
    result = base.render.find(f"**/{search}")
    if result.isEmpty():
        raise ValueError(f"Node not found: {path}")
    return result


def _vec3(v: Any) -> list[float]:
    return [round(v.getX(), 4), round(v.getY(), 4), round(v.getZ(), 4)]


def _node_info(np: Any) -> dict:
    return {
        "name": np.getName(),
        "path": str(np),
        "pos": _vec3(np.getPos()),
        "hpr": _vec3(np.getHpr()),
        "scale": _vec3(np.getScale()),
        "type": np.getPythonTag("p3d_type") or "node",
        "children": np.getNumChildren(),
        "visible": not np.isHidden(),
    }


@rpc("node.ls")
def node_ls(params: dict, base: Any) -> dict:
    np = _resolve_node(params.get("path", "/render"), base)
    children = [{"name": c.getName(), "type": c.getPythonTag("p3d_type") or "node"} for c in np.getChildren()]
    return {"path": str(np), "children": children}


@rpc("node.tree")
def node_tree(params: dict, base: Any) -> dict:
    np = _resolve_node(params.get("path", "/render"), base)
    return {"tree": _build_tree(np, params.get("depth", 10), 0)}


def _build_tree(np: Any, max_depth: int, current: int) -> dict:
    node = {"name": np.getName(), "type": np.getPythonTag("p3d_type") or "node"}
    if current < max_depth:
        children = [_build_tree(c, max_depth, current + 1) for c in np.getChildren()]
        if children:
            node["children"] = children
    return node


@rpc("node.get")
def node_get(params: dict, base: Any) -> dict:
    return _node_info(_resolve_node(params["path"], base))


@rpc("node.set")
def node_set(params: dict, base: Any) -> dict:
    np = _resolve_node(params["path"], base)
    if "pos" in params:
        np.setPos(Vec3(*params["pos"]))
    if "hpr" in params:
        np.setHpr(Vec3(*params["hpr"]))
    if "scale" in params:
        s = params["scale"]
        np.setScale(Vec3(*s) if isinstance(s, (list, tuple)) else s)
    if "color" in params:
        np.setColor(Vec4(*params["color"]))
    if "visible" in params:
        np.show() if params["visible"] else np.hide()
    return _node_info(np)


@rpc("node.add")
def node_add(params: dict, base: Any) -> dict:
    from p3d.core.scene_builder import build_node
    parent = _resolve_node(params.get("parent", "/render"), base)
    np = build_node(params, parent, base)
    return _node_info(np)


@rpc("node.rm")
def node_rm(params: dict, base: Any) -> dict:
    np = _resolve_node(params["path"], base)
    name = np.getName()
    np.removeNode()
    return {"removed": name}


@rpc("node.find")
def node_find(params: dict, base: Any) -> dict:
    results = base.render.findAllMatches(f"**/{params['pattern']}")
    nodes = [_node_info(np) for np in results]
    return {"matches": nodes, "count": len(nodes)}


@rpc("camera.get")
def camera_get(params: dict, base: Any) -> dict:
    if base.camera is None:
        return {"error": "no camera in headless mode"}
    result = {"pos": _vec3(base.camera.getPos()), "hpr": _vec3(base.camera.getHpr())}
    lens = getattr(base, 'camLens', None)
    if lens:
        result["fov"] = round(lens.getFov()[0], 1)
        result["near"] = round(lens.getNear(), 4)
        result["far"] = round(lens.getFar(), 1)
    return result


@rpc("camera.set")
def camera_set(params: dict, base: Any) -> dict:
    if base.camera is None:
        raise ValueError("no camera in headless mode")
    if "pos" in params:
        base.camera.setPos(Vec3(*params["pos"]))
    if "hpr" in params:
        base.camera.setHpr(Vec3(*params["hpr"]))
    if "look_at" in params:
        base.camera.lookAt(Vec3(*params["look_at"]))
    lens = getattr(base, 'camLens', None)
    if lens:
        for key, setter in [("fov", lens.setFov), ("near", lens.setNear), ("far", lens.setFar)]:
            if key in params:
                setter(params[key])
    return camera_get({}, base)


@rpc("light.add")
def light_add(params: dict, base: Any) -> dict:
    from p3d.core.scene_builder import build_light
    build_light(params, base)
    return {"ok": True, "name": params.get("name", "light")}


@rpc("light.ls")
def light_ls(params: dict, base: Any) -> dict:
    from p3d.core.scene_serializer import serialize_light
    return {"lights": [serialize_light(lnp) for lnp in base.render.findAllMatches("**/+Light")]}


@rpc("light.rm")
def light_rm(params: dict, base: Any) -> dict:
    name = params["name"]
    for lnp in base.render.findAllMatches("**/+Light"):
        if lnp.getName() == name:
            base.render.clearLight(lnp)
            lnp.removeNode()
            return {"removed": name}
    raise ValueError(f"Light not found: {name}")


@rpc("light.set")
def light_set(params: dict, base: Any) -> dict:
    name = params["name"]
    for lnp in base.render.findAllMatches("**/+Light"):
        if lnp.getName() == name:
            if "color" in params:
                lnp.node().setColor(Vec4(*params["color"]))
            if "pos" in params:
                lnp.setPos(Vec3(*params["pos"]))
            if "direction" in params:
                lnp.setHpr(Vec3(*params["direction"]))
            return {"ok": True, "name": name}
    raise ValueError(f"Light not found: {name}")


@rpc("scene.load")
def scene_load(params: dict, base: Any) -> dict:
    from p3d.core.scene_builder import load_scene_yaml, build_scene
    scene_data = load_scene_yaml(params["path"])
    build_scene(scene_data, base)
    return {"ok": True, "scene": scene_data.get("name", "unknown")}


@rpc("scene.save")
def scene_save(params: dict, base: Any) -> dict:
    from p3d.core.scene_serializer import save_scene_yaml
    save_scene_yaml(base, params["path"])
    return {"ok": True, "path": params["path"]}


@rpc("render.frame")
def render_frame(params: dict, base: Any) -> dict:
    count = params.get("count", 1)
    for _ in range(count):
        base.taskMgr.step()
    return {"rendered": count}


@rpc("render.set")
def render_set(params: dict, base: Any) -> dict:
    prop, val = params["prop"], params["val"]
    if prop in ("bg-color", "background_color"):
        if isinstance(val, (list, tuple)):
            base.setBackgroundColor(Vec4(*val))
        return {"ok": True}
    if prop == "wireframe":
        base.render.setRenderModeWireframe() if val else base.render.clearRenderMode()
        return {"ok": True}
    if prop == "fps-meter":
        if base.win is None:
            raise ValueError("fps-meter not available in headless mode")
        base.setFrameRateMeter(bool(val))
        return {"ok": True}
    raise ValueError(f"Unknown render property: {prop}")


@rpc("screenshot")
def screenshot(params: dict, base: Any) -> dict:
    out_path = Path(params.get("output", "screenshot.png"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = base.screenshot(namePrefix=str(out_path), defaultFilename=0)
    return {"ok": result is not None, "path": str(out_path.resolve())}


@rpc("script.attach")
def script_attach(params: dict, base: Any) -> dict:
    np = _resolve_node(params["path"], base)
    script_file = Path(params["script"]).resolve()
    if not script_file.exists():
        raise FileNotFoundError(f"Script not found: {params['script']}")

    spec = importlib.util.spec_from_file_location(script_file.stem, script_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[script_file.stem] = mod
    spec.loader.exec_module(mod)

    from p3d.core.script import Script
    script_cls = next(
        (getattr(mod, a) for a in dir(mod)
         if isinstance(getattr(mod, a), type) and issubclass(getattr(mod, a), Script) and getattr(mod, a) is not Script),
        None,
    )
    if not script_cls:
        raise ValueError(f"No Script subclass found in {params['script']}")

    instance = script_cls(np, base)
    instance._activate()

    scripts = np.getPythonTag("p3d_active_scripts") or []
    scripts.append({"path": str(params["script"]), "instance": instance})
    np.setPythonTag("p3d_active_scripts", scripts)
    return {"ok": True, "script": script_cls.__name__, "node": str(np)}


@rpc("script.detach")
def script_detach(params: dict, base: Any) -> dict:
    np = _resolve_node(params["path"], base)
    scripts = np.getPythonTag("p3d_active_scripts") or []
    remaining, removed = [], False
    for s in scripts:
        if s["path"] == params["script"]:
            s["instance"]._deactivate()
            removed = True
        else:
            remaining.append(s)
    np.setPythonTag("p3d_active_scripts", remaining)
    if not removed:
        raise ValueError(f"Script {params['script']} not attached to {params['path']}")
    return {"ok": True}


@rpc("script.list")
def script_list(params: dict, base: Any) -> dict:
    np = _resolve_node(params.get("path", "/render"), base)
    scripts = np.getPythonTag("p3d_active_scripts") or []
    return {"scripts": [{"path": s["path"], "class": s["instance"].__class__.__name__} for s in scripts]}


@rpc("script.run")
def script_run(params: dict, base: Any) -> dict:
    script_file = Path(params["script"]).resolve()
    if not script_file.exists():
        raise FileNotFoundError(f"Script not found: {params['script']}")
    exec_globals = {"base": base, "render": base.render, "loader": base.loader, "taskMgr": base.taskMgr}
    exec(compile(script_file.read_text(), str(script_file), "exec"), exec_globals)
    return {"ok": True, "script": str(params["script"])}


@rpc("config.get")
def config_get(params: dict, base: Any) -> dict:
    from panda3d.core import ConfigVariableManager, ConfigVariableString
    key = params.get("key")
    if key:
        return {"key": key, "value": ConfigVariableString(key, "").getValue()}
    mgr = ConfigVariableManager.getGlobalPtr()
    count = mgr.getNumVariables()
    config = {mgr.getVariable(i).getName(): mgr.getVariable(i).getStringValue() for i in range(min(count, 100))}
    return {"config": config, "total": count}


@rpc("config.set")
def config_set(params: dict, base: Any) -> dict:
    from panda3d.core import loadPrcFileData
    loadPrcFileData("p3d-runtime", f"{params['key']} {params['val']}")
    return {"ok": True, "key": params["key"], "val": str(params["val"])}
