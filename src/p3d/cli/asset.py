"""p3d asset — asset management commands."""

from __future__ import annotations

from pathlib import Path

import click

from p3d.cli._util import require_project


ASSET_EXTENSIONS = {
    "model": {".egg", ".bam", ".gltf", ".glb", ".fbx", ".obj", ".dae"},
    "texture": {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".tif", ".dds"},
    "sound": {".ogg", ".wav", ".mp3", ".flac"},
    "font": {".ttf", ".otf"},
    "shader": {".glsl", ".vert", ".frag", ".sha"},
}

ALL_EXTENSIONS = set()
for exts in ASSET_EXTENSIONS.values():
    ALL_EXTENSIONS |= exts


def _classify(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, exts in ASSET_EXTENSIONS.items():
        if suffix in exts:
            return category
    return "other"


@click.group()
def asset():
    """Manage project assets."""
    pass


@asset.command("list")
@click.option("--type", "asset_type", default=None,
              type=click.Choice(["model", "texture", "sound", "font", "shader"]),
              help="Filter by asset type.")
def asset_list(asset_type: str | None):
    """List project assets."""
    pm = require_project()
    assets_dir = pm.project_dir / "assets"
    if not assets_dir.exists():
        click.echo("No assets/ directory.")
        return

    files = sorted(assets_dir.rglob("*"))
    for f in files:
        if not f.is_file():
            continue
        cat = _classify(f)
        if asset_type and cat != asset_type:
            continue
        rel = f.relative_to(pm.project_dir)
        click.echo(f"  [{cat:8s}] {rel}")


@asset.command("info")
@click.argument("file")
def asset_info(file: str):
    """Show asset file information."""
    pm = require_project()
    path = pm.resolve(file)
    if not path.exists():
        click.echo(f"Error: {file} not found.", err=True)
        raise SystemExit(1)

    cat = _classify(path)
    size = path.stat().st_size
    click.echo(f"  File:     {path.relative_to(pm.project_dir)}")
    click.echo(f"  Type:     {cat}")
    click.echo(f"  Format:   {path.suffix}")
    click.echo(f"  Size:     {_human_size(size)}")


@asset.command("convert")
@click.argument("src")
@click.argument("dst")
def asset_convert(src: str, dst: str):
    """Convert between model formats (egg/bam/gltf)."""
    import subprocess
    import shutil

    pm = require_project()
    src_path = pm.resolve(src)
    dst_path = pm.resolve(dst)

    if not src_path.exists():
        click.echo(f"Error: {src} not found.", err=True)
        raise SystemExit(1)

    src_ext = src_path.suffix.lower()
    dst_ext = dst_path.suffix.lower()

    # Map conversion to pandatool commands
    converters = {
        (".egg", ".bam"): "egg2bam",
        (".bam", ".egg"): "bam2egg",
        (".gltf", ".egg"): "gltf2egg",
        (".gltf", ".bam"): "gltf2bam",
        (".glb", ".egg"): "gltf2egg",
        (".glb", ".bam"): "gltf2bam",
    }

    converter = converters.get((src_ext, dst_ext))
    if not converter:
        click.echo(f"Error: no converter for {src_ext} -> {dst_ext}.", err=True)
        raise SystemExit(1)

    if not shutil.which(converter):
        click.echo(f"Error: '{converter}' not found in PATH. Install panda3d-tools.", err=True)
        raise SystemExit(1)

    result = subprocess.run([converter, "-o", str(dst_path), str(src_path)], capture_output=True, text=True)
    if result.returncode != 0:
        click.echo(f"Error: {result.stderr.strip()}", err=True)
        raise SystemExit(1)
    click.echo(f"Converted: {src} -> {dst}")


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
