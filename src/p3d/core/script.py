"""Script base class — attach behaviors to scene graph nodes."""

from __future__ import annotations

from typing import Any

from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import ClockObject


class Script(DirectObject):
    """Base class for behavior scripts attached to nodes.

    Subclass and override start(), update(dt), cleanup().
    """

    def __init__(self, node: Any, base: Any):
        super().__init__()
        self.node = node
        self.base = base
        self._task_name = f"script-{self.__class__.__name__}-{id(self)}"

    def _activate(self) -> None:
        self.start()
        self.base.taskMgr.add(self._update_task, self._task_name)

    def _deactivate(self) -> None:
        self.cleanup()
        self.base.taskMgr.remove(self._task_name)
        self.ignoreAll()

    def _update_task(self, task: Any) -> int:
        self.update(ClockObject.getGlobalClock().getDt())
        return Task.cont

    def start(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def cleanup(self) -> None:
        pass
