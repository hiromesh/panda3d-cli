"""p3d train — AI/RL training commands."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import click

from p3d.cli._util import require_project


@click.group()
def train():
    """AI/RL training commands."""
    pass


@train.command("start")
@click.argument("env_file")
@click.option("--episodes", default=100, help="Number of episodes.")
@click.option("--render", is_flag=True, help="Render during training.")
def train_start(env_file: str, episodes: int, render: bool):
    """Start RL training with a Gymnasium environment."""
    try:
        import gymnasium
    except ImportError:
        click.echo("Error: gymnasium not installed. Run: pip install gymnasium", err=True)
        raise SystemExit(1)

    pm = require_project()
    env_path = pm.resolve(env_file)
    if not env_path.exists():
        click.echo(f"Error: {env_file} not found.", err=True)
        raise SystemExit(1)

    env_cls = _load_env_class(env_path)
    if not env_cls:
        click.echo(f"Error: no Gymnasium Env subclass found in {env_file}.", err=True)
        raise SystemExit(1)

    render_mode = "human" if render else None
    env = env_cls(render_mode=render_mode)

    click.echo(f"Training {env_cls.__name__} for {episodes} episodes...")
    for ep in range(episodes):
        obs, info = env.reset()
        total_reward = 0.0
        done = False
        steps = 0
        while not done:
            action = env.action_space.sample()  # Random policy
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated
        if (ep + 1) % 10 == 0 or ep == 0:
            click.echo(f"  Episode {ep + 1}/{episodes}: reward={total_reward:.2f} steps={steps}")

    env.close()
    click.echo("Training complete.")


@train.command("eval")
@click.argument("env_file")
@click.option("--episodes", default=10, help="Number of episodes.")
@click.option("--render", is_flag=True, default=True, help="Render during evaluation.")
def train_eval(env_file: str, episodes: int, render: bool):
    """Evaluate a policy (random by default) with rendering."""
    try:
        import gymnasium
    except ImportError:
        click.echo("Error: gymnasium not installed.", err=True)
        raise SystemExit(1)

    pm = require_project()
    env_path = pm.resolve(env_file)
    env_cls = _load_env_class(env_path)
    if not env_cls:
        click.echo(f"Error: no Env subclass found in {env_file}.", err=True)
        raise SystemExit(1)

    env = env_cls(render_mode="human" if render else None)
    click.echo(f"Evaluating {env_cls.__name__}...")

    for ep in range(episodes):
        obs, info = env.reset()
        total_reward = 0.0
        done = False
        steps = 0
        while not done:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated
        click.echo(f"  Episode {ep + 1}: reward={total_reward:.2f} steps={steps}")

    env.close()


def _load_env_class(path: Path):
    """Load and return the first Gymnasium Env subclass from a file."""
    import gymnasium

    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)

    for attr_name in dir(mod):
        attr = getattr(mod, attr_name)
        if isinstance(attr, type) and issubclass(attr, gymnasium.Env) and attr is not gymnasium.Env:
            return attr
    return None
