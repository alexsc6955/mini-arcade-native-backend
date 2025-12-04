"""
mini-arcade native backend package.
"""

from __future__ import annotations

import os
import sys
import time

# --- 1) Make sure Windows can find SDL2.dll when using vcpkg ------------------

if sys.platform == "win32":
    vcpkg_root = os.environ.get("VCPKG_ROOT")
    if vcpkg_root:
        # Typical vcpkg layout: <VCPKG_ROOT>/installed/x64-windows/bin/SDL2.dll
        sdl_bin = os.path.join(vcpkg_root, "installed", "x64-windows", "bin")
        if os.path.isdir(sdl_bin):
            # Python 3.8+ – add DLL search path before importing the extension
            os.add_dll_directory(sdl_bin)

# --- 2) Now import native extension and core types ----------------------------

from mini_arcade_core import Backend, Event, EventType, Game, GameConfig, Scene

from . import _native as native

# --- 2) Now import core + define NativeBackend as before ---


__all__ = ["NativeBackend", "native"]


_NATIVE_TO_CORE = {
    native.EventType.Unknown: EventType.UNKNOWN,
    native.EventType.Quit: EventType.QUIT,
    native.EventType.KeyDown: EventType.KEYDOWN,
    native.EventType.KeyUp: EventType.KEYUP,
}


class NativeBackend(Backend):
    """Adapter that makes the C++ Engine usable as a mini-arcade backend."""

    def __init__(self):
        self._engine = native.Engine()

    def init(self, width: int, height: int, title: str):
        """
        Initialize the backend with a window of given width, height, and title.

        :param width: Width of the window in pixels.
        :type width: int

        :param height: Height of the window in pixels.
        :type height: int

        :param title: Title of the window.
        :type title: str
        """
        self._engine.init(width, height, title)

    def poll_events(self) -> list[Event]:
        """
        Poll for events from the backend and return them as a list of Event objects.

        :return: List of Event objects representing the polled events.
        :rtype: list[Event]
        """
        events: list[Event] = []
        for ev in self._engine.poll_events():
            core_type = _NATIVE_TO_CORE.get(ev.type, EventType.UNKNOWN)
            key = ev.key if getattr(ev, "key", 0) != 0 else None
            events.append(Event(type=core_type, key=key))
        return events

    def begin_frame(self):
        """Begin a new frame for rendering."""
        self._engine.begin_frame()

    def end_frame(self):
        """End the current frame for rendering."""
        self._engine.end_frame()

    def draw_rect(self, x: int, y: int, w: int, h: int):
        """
        Draw a rectangle at the specified position with given width and height.

        :param x: X coordinate of the rectangle's top-left corner.
        :type x: int

        :param y: Y coordinate of the rectangle's top-left corner.
        :type y: int

        :param w: Width of the rectangle.
        :type w: int

        :param h: Height of the rectangle.
        :type h: int
        """
        self._engine.draw_rect(x, y, w, h)


class NativeGame(Game):
    """Game class using the NativeBackend by default."""

    def __init__(self, config: GameConfig):
        super().__init__(config)
        self.backend = NativeBackend()

    def change_scene(self, scene: Scene):
        """
        Swap the active scene. Concrete implementations should call
        ``on_exit``/``on_enter`` appropriately.

        :param scene: The new scene to activate.
        :type scene: Scene
        """
        if self._current_scene is not None:
            self._current_scene.on_exit()

        self._current_scene = scene
        self._current_scene.on_enter()

    def run(self, initial_scene: Scene):
        """
        Run the main loop starting with the given scene.

        This is intentionally left abstract so you can plug pygame, pyglet,
        or another backend.

        :param initial_scene: The scene to start the game with.
        :type initial_scene: Scene
        """
        if self.backend is None:
            raise RuntimeError(
                "GameConfig.backend must be set before running the game."
            )

        backend = self.backend

        # Init backend window
        backend.init(self.config.width, self.config.height, self.config.title)

        # Set the initial scene
        self.change_scene(initial_scene)

        self._running = True

        target_dt = (
            1.0 / float(self.config.fps) if self.config.fps > 0 else 0.0
        )
        last_time = time.perf_counter()

        while self._running:
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            # 1) Poll events and pass to scene
            events = list(backend.poll_events())
            if self._current_scene is not None:
                for ev in events:
                    self._current_scene.handle_event(ev)  # type: ignore[arg-type]

                # 2) Update scene
                self._current_scene.update(dt)

                # 3) Draw
                backend.begin_frame()
                self._current_scene.draw(backend)
                backend.end_frame()

            # Simple FPS cap
            if target_dt > 0 and dt < target_dt:
                time.sleep(target_dt - dt)
