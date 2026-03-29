"""CLI entry point — main click group with all commands."""

import click

from p3d.cli.init_cmd import init
from p3d.cli.run import run, stop, status
from p3d.cli.screenshot import screenshot
from p3d.cli.scene import scene
from p3d.cli.node import node
from p3d.cli.camera import camera
from p3d.cli.light import light
from p3d.cli.render import render
from p3d.cli.script_cmd import script
from p3d.cli.asset import asset
from p3d.cli.config import config
from p3d.cli.train import train


@click.group()
@click.version_option(package_name="panda3d-cli")
def main():
    """p3d — CLI tool for operating Panda3D game engine."""
    pass


main.add_command(init)
main.add_command(run)
main.add_command(stop)
main.add_command(status)
main.add_command(screenshot)
main.add_command(scene)
main.add_command(node)
main.add_command(camera)
main.add_command(light)
main.add_command(render)
main.add_command(script)
main.add_command(asset)
main.add_command(config)
main.add_command(train)
