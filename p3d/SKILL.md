---
name: p3d
description: Operate the Panda3D 3D game engine from the terminal. Use this skill when working on any p3d project — building scenes, inspecting scene graphs, controlling cameras/lights, running scripts, or debugging a running game.
---

# p3d — Panda3D Game Engine CLI

Operate the Panda3D 3D game engine from the terminal. Build, run, inspect, and modify 3D games.

## Quick Start

```bash
p3d init my-game && cd my-game    # Create project
p3d run                            # Start game (opens window)
p3d status                         # Check runtime status
p3d screenshot shot.png            # Capture frame
p3d stop                           # Stop game
```

## Project Structure

```
my-game/
├── p3d.yaml              # Project config (window, render, physics)
├── main.py                # Game entry point (ShowBase subclass)
├── scenes/                # Scene YAML files (declarative scene description)
├── scripts/               # Behavior scripts (Python, attached to nodes)
├── assets/{models,textures,sounds,fonts,shaders}/
├── envs/                  # Gymnasium RL environments
└── .p3d/                  # Runtime (socket, PID, cache — gitignored)
```

## Commands

### Lifecycle

| Command | Description |
|---------|-------------|
| `p3d init <name>` | Create new project |
| `p3d run [--headless] [--offscreen]` | Start game |
| `p3d stop` | Stop game |
| `p3d status` | Show PID, FPS, node count |
| `p3d screenshot <file.png>` | Capture frame |

### Scene Management

| Command | Description |
|---------|-------------|
| `p3d scene list` | List scene YAML files |
| `p3d scene load <file.yaml>` | Load scene into running game |
| `p3d scene save <file.yaml>` | Export current scene to YAML |
| `p3d scene validate <file.yaml>` | Validate YAML format (offline) |

### Node Operations (runtime — game must be running)

| Command | Description |
|---------|-------------|
| `p3d node ls [--path /render/...]` | List children of a node |
| `p3d node tree [--depth N]` | Print scene graph tree |
| `p3d node get <path>` | Get node properties (pos, hpr, scale) |
| `p3d node set <path> --pos x,y,z --hpr h,p,r --scale s` | Set properties |
| `p3d node add <parent> --model <file> --name <n>` | Add model to scene |
| `p3d node rm <path>` | Remove node |
| `p3d node find <pattern>` | Find nodes by name |

### Camera

| Command | Description |
|---------|-------------|
| `p3d camera get` | Get camera pos/hpr/fov |
| `p3d camera set --pos x,y,z --look-at x,y,z --fov N` | Set camera |

### Lights

| Command | Description |
|---------|-------------|
| `p3d light add <ambient\|directional\|point\|spot> --name N --color r,g,b,a` | Add light |
| `p3d light ls` | List lights |
| `p3d light rm <name>` | Remove light |
| `p3d light set <name> --color r,g,b,a --pos x,y,z` | Modify light |

### Render Control

| Command | Description |
|---------|-------------|
| `p3d render frame --count N` | Render N frames |
| `p3d render set <prop> <val>` | Set render property (bg-color, wireframe, fps-meter) |

### Scripts

| Command | Description |
|---------|-------------|
| `p3d script attach <node-path> <script.py>` | Attach behavior to node |
| `p3d script detach <node-path> <script.py>` | Remove behavior |
| `p3d script list [--path <node>]` | List attached scripts |
| `p3d script run <script.py>` | Execute arbitrary Python in game context |

### Assets

| Command | Description |
|---------|-------------|
| `p3d asset list [--type model\|texture\|sound]` | List assets |
| `p3d asset info <file>` | Show file info |
| `p3d asset convert <src> <dst>` | Convert formats (egg/bam/gltf) |

### Config

| Command | Description |
|---------|-------------|
| `p3d config get [key]` | Get runtime config |
| `p3d config set <key> <val>` | Set runtime config |

### AI/RL Training

| Command | Description |
|---------|-------------|
| `p3d train start <env.py> --episodes N [--render]` | Run RL training |
| `p3d train eval <env.py> --episodes N [--render]` | Evaluate policy |

## Scene YAML Format

```yaml
scene:
  name: level_1

  lights:
    - name: sun
      type: directional
      color: [0.9, 0.9, 0.8, 1.0]
      direction: [1, 1, -2]
    - name: ambient
      type: ambient
      color: [0.3, 0.3, 0.4, 1.0]

  nodes:
    - name: ground
      model: assets/models/ground.egg
      pos: [0, 0, 0]
      scale: 10
      tags: {walkable: "true"}

    - name: player
      type: actor                   # animated model
      model: assets/models/char.egg
      animations:
        walk: assets/models/char-walk.egg
        idle: assets/models/char-idle.egg
      pos: [0, 0, 0]
      scripts:
        - scripts/player_ctrl.py

    - name: objects
      pos: [5, 0, 0]
      children:                     # nested nodes
        - name: box
          model: assets/models/box.egg

  camera:
    pos: [0, -20, 10]
    look_at: [0, 0, 2]
    fov: 60
```

Node types: `model` (default, static), `actor` (animated), `group` (empty, omit model).

## Behavior Script Template

```python
from p3d.core.script import Script

class MyBehavior(Script):
    def start(self):
        """Called once. self.node = target NodePath, self.base = ShowBase."""
        self.speed = 10.0
        self.accept('w', self.on_w)

    def update(self, dt):
        """Called every frame."""
        pass

    def cleanup(self):
        """Called on detach."""
        self.ignore_all()
```

## Typical Workflows

### Build a game from scratch

```bash
p3d init my-game && cd my-game
# Edit scenes/main.scene.yaml — add models, lights
# Write scripts/player.py — game logic
# Write main.py — custom ShowBase subclass if needed
p3d run
p3d screenshot check.png           # verify visuals
p3d node tree                      # debug scene graph
p3d stop
```

### Iterate on a running game

```bash
p3d run
p3d node add /render --model assets/models/tree.egg --name tree1 --pos 5,0,0
p3d camera set --pos 0,-30,15 --look-at 0,0,0
p3d light set sun --color 1,0.8,0.6,1
p3d screenshot after_tweaks.png
p3d scene save scenes/tweaked.scene.yaml   # persist changes
p3d stop
```

### Run arbitrary Python in game

```bash
cat > scripts/debug.py << 'EOF'
print("Nodes:", len(render.findAllMatches("**")))
for node in render.getChildren():
    print(f"  {node.getName()}: pos={node.getPos()}")
EOF

p3d script run scripts/debug.py
```
