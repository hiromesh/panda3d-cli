"""Scene serializer — dumps a Panda3D scene graph to a YAML-compatible dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def serialize_scene(base: Any) -> dict:
    scene: dict[str, Any] = {"name": "exported"}

    lights = [serialize_light(lnp) for lnp in base.render.findAllMatches("**/+Light")]
    if lights:
        scene["lights"] = lights

    light_types = {"AmbientLight", "DirectionalLight", "PointLight", "Spotlight"}
    nodes = [_serialize_node(c) for c in base.render.getChildren() if c.node().getClassType().getName() not in light_types]
    if nodes:
        scene["nodes"] = nodes

    if base.camera is not None:
        cam: dict[str, Any] = {"pos": _vec3(base.camera.getPos()), "hpr": _vec3(base.camera.getHpr())}
        if hasattr(base, 'camLens') and base.camLens:
            cam["fov"] = round(base.camLens.getFov()[0], 1)
        scene["camera"] = cam

    return {"scene": scene}


def save_scene_yaml(base: Any, path: str | Path) -> None:
    with open(path, "w") as f:
        yaml.dump(serialize_scene(base), f, default_flow_style=False, sort_keys=False)


def serialize_light(lnp: Any) -> dict:
    light = lnp.node()
    class_name = light.getClassType().getName()
    type_map = {"AmbientLight": "ambient", "DirectionalLight": "directional", "PointLight": "point", "Spotlight": "spot"}
    result: dict[str, Any] = {
        "name": lnp.getName(),
        "type": lnp.getPythonTag("p3d_light_type") or type_map.get(class_name, "unknown"),
        "color": _vec4(light.getColor()),
    }
    if class_name in ("PointLight", "Spotlight"):
        result["pos"] = _vec3(lnp.getPos())
    if class_name == "DirectionalLight":
        result["direction"] = _vec3(lnp.getHpr())
    return result


def _serialize_node(np: Any) -> dict:
    result: dict[str, Any] = {"name": np.getName()}
    p3d_type = np.getPythonTag("p3d_type")
    if p3d_type == "actor":
        result["type"] = "actor"

    pos = np.getPos()
    if pos.length() > 0.001:
        result["pos"] = _vec3(pos)
    hpr = np.getHpr()
    if hpr.length() > 0.001:
        result["hpr"] = _vec3(hpr)
    scale = np.getScale()
    if abs(scale.getX() - 1) > 0.001 or abs(scale.getY() - 1) > 0.001 or abs(scale.getZ() - 1) > 0.001:
        result["scale"] = round(scale.getX(), 4) if scale.getX() == scale.getY() == scale.getZ() else _vec3(scale)

    scripts = np.getPythonTag("p3d_scripts")
    if scripts:
        result["scripts"] = list(scripts)

    children = [_serialize_node(c) for c in np.getChildren()]
    if children:
        result["children"] = children
    return result


def _vec3(v: Any) -> list[float]:
    return [round(v.getX(), 4), round(v.getY(), 4), round(v.getZ(), 4)]


def _vec4(v: Any) -> list[float]:
    return [round(v.getX(), 4), round(v.getY(), 4), round(v.getZ(), 4), round(v.getW(), 4)]
