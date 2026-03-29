"""Scene builder — constructs Panda3D scene graph from a YAML scene dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from panda3d.core import Vec3, Vec4


def load_scene_yaml(path: str | Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("scene", data)


def build_scene(scene_data: dict, base: Any) -> None:
    base.render.getChildren().detach()
    for light_def in scene_data.get("lights", []):
        build_light(light_def, base)
    for node_def in scene_data.get("nodes", []):
        build_node(node_def, base.render, base)
    cam = scene_data.get("camera")
    if cam and base.camera is not None:
        _apply_camera(cam, base)


def build_light(light_def: dict, base: Any) -> None:
    from panda3d.core import AmbientLight, DirectionalLight, PointLight, Spotlight

    name = light_def.get("name", "light")
    ltype = light_def.get("type", "ambient")
    color = Vec4(*light_def.get("color", [1, 1, 1, 1]))

    constructors = {
        "ambient": AmbientLight,
        "directional": DirectionalLight,
        "point": PointLight,
        "spot": Spotlight,
    }
    cls = constructors.get(ltype)
    if not cls:
        return

    light = cls(name)
    light.setColor(color)
    lnp = base.render.attachNewNode(light)
    lnp.setPythonTag("p3d_light_type", ltype)

    if ltype == "directional":
        d = light_def.get("direction", [0, 0, -1])
        lnp.setHpr(Vec3(*d))
    elif ltype in ("point", "spot"):
        lnp.setPos(*light_def.get("pos", [0, 0, 0]))
        if ltype == "point" and "attenuation" in light_def:
            light.setAttenuation(Vec3(*light_def["attenuation"]))
        if ltype == "spot":
            d = light_def.get("direction", [0, 0, -1])
            lnp.lookAt(lnp.getPos() + Vec3(*d))
            if "fov" in light_def:
                light.getLens().setFov(light_def["fov"])

    base.render.setLight(lnp)


def build_node(node_def: dict, parent: Any, base: Any) -> Any:
    name = node_def.get("name", "node")
    node_type = node_def.get("type", "model")
    model_path = node_def.get("model")

    if node_type == "actor" and model_path:
        from direct.actor.Actor import Actor
        np = Actor(model_path, node_def.get("animations", {}))
        np.reparentTo(parent)
        np.setName(name)
        np.setPythonTag("p3d_type", "actor")
    elif model_path:
        np = base.loader.loadModel(model_path)
        np.reparentTo(parent)
        np.setName(name)
        np.setPythonTag("p3d_type", "model")
    else:
        np = parent.attachNewNode(name)
        np.setPythonTag("p3d_type", "group")

    if "pos" in node_def:
        np.setPos(Vec3(*node_def["pos"]))
    if "hpr" in node_def:
        np.setHpr(Vec3(*node_def["hpr"]))
    if "scale" in node_def:
        s = node_def["scale"]
        np.setScale(Vec3(*s) if isinstance(s, (list, tuple)) else s)
    if "color" in node_def:
        np.setColor(Vec4(*node_def["color"]))

    for tag_name, tag_val in node_def.get("tags", {}).items():
        np.setTag(tag_name, str(tag_val))

    scripts = node_def.get("scripts", [])
    if scripts:
        np.setPythonTag("p3d_scripts", scripts)

    for child_def in node_def.get("children", []):
        build_node(child_def, np, base)

    return np


def _apply_camera(cam_def: dict, base: Any) -> None:
    if "pos" in cam_def:
        base.camera.setPos(Vec3(*cam_def["pos"]))
    if "look_at" in cam_def:
        base.camera.lookAt(Vec3(*cam_def["look_at"]))
    if "hpr" in cam_def:
        base.camera.setHpr(Vec3(*cam_def["hpr"]))
    lens = getattr(base, 'camLens', None)
    if lens:
        for key, setter in [("fov", lens.setFov), ("near", lens.setNear), ("far", lens.setFar)]:
            if key in cam_def:
                setter(cam_def[key])
