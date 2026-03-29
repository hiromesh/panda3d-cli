# panda3d-cli

A CLI wrapper for [Panda3D](https://www.panda3d.org/) that lets any AI agent (or human) operate a 3D game engine from the terminal — no GUI required.

## Why

Most game engines assume a human sitting in a GUI editor. This tool treats the engine as a platform: a running game process you talk to over a socket, with every operation exposed as a shell command. AI agents, scripts, and CI pipelines can all drive it.

## Requirements

- Python 3.10+
- panda3d >= 1.10.14

## Install

```bash
pip install panda3d-cli
```

### AI Skill (optional)

The full command reference is available as an AI skill at `p3d/SKILL.md`. Install it in your AI coding assistant to enable `/p3d` as a slash command.

## Quick Start

```bash
p3d init my-game && cd my-game
p3d run
p3d status
p3d screenshot check.png
p3d stop
```

## How It Works

`p3d run` spawns a Panda3D subprocess. All subsequent commands connect to it over a Unix domain socket using JSON-RPC 2.0. The socket server runs as a Panda3D task — non-blocking, no impact on the render loop.

```
p3d <cmd>  ──── Unix socket (JSON-RPC) ────►  game process (Panda3D)
```

## Commands

| Group | Commands |
|-------|----------|
| Lifecycle | `init`, `run`, `stop`, `status`, `screenshot` |
| Scene | `scene list/load/save/validate` |
| Nodes | `node ls/tree/get/set/add/rm/find` |
| Camera | `camera get/set` |
| Lights | `light add/ls/rm/set` |
| Render | `render frame/set` |
| Scripts | `script attach/detach/list/run` |
| Assets | `asset list/info/convert` |
| Config | `config get/set` |
| RL Training | `train start/eval` |

Full command reference: see `p3d/SKILL.md` or run `p3d <command> --help`.

## Project Layout

```
my-game/
├── p3d.yaml          # window, render, physics config
├── main.py           # optional ShowBase subclass
├── scenes/           # declarative scene YAML files
├── scripts/          # behavior scripts (attach to nodes at runtime)
├── assets/           # models, textures, sounds, shaders
└── envs/             # Gymnasium RL environments
```

## Modes

| Flag | Use case |
|------|----------|
| _(none)_ | Normal windowed game |
| `--headless` | No window, no GPU — servers, CI |
| `--offscreen` | Offscreen buffer — screenshot/video capture |

## Behavior Scripts

Attach Python scripts to scene nodes at runtime:

```python
from p3d.core.script import Script

class Spin(Script):
    def update(self, dt):
        self.node.setH(self.node.getH() + 90 * dt)
```

```bash
p3d script attach /render/cube scripts/spin.py
```

## RL / Gymnasium

```python
from p3d.env import Panda3DEnv

class MyEnv(Panda3DEnv):
    def reset(self): ...
    def step(self, action): ...
    def _get_obs(self): ...
    def _compute_reward(self): ...
```

```bash
p3d train start envs/my_env.py --episodes 1000
```

## Escape Hatch

Anything not covered by a command — run arbitrary Python inside the live game process:

```bash
p3d script run scripts/anything.py
```
