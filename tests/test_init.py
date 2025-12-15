import importlib
import os
import sys
import types
from dataclasses import dataclass

import pytest


def setup_fake_core_and_native(monkeypatch):
    """
    Inject fake mini_arcade_core and mini_arcade_native_backend._native modules
    into sys.modules so we can import the package without the real C++ extension.
    """
    # --- Fake mini_arcade_core -------------------------------------------------
    fake_core = types.ModuleType("mini_arcade_core")

    class FakeBackend:
        """Minimal base class just to satisfy inheritance."""

    class FakeCoreEventType:
        UNKNOWN = "core_unknown"
        QUIT = "core_quit"
        KEYDOWN = "core_keydown"
        KEYUP = "core_keyup"
        MOUSEMOTION = "core_mousemotion"
        MOUSEBUTTONDOWN = "core_mousebuttondown"
        MOUSEBUTTONUP = "core_mousebuttonup"
        MOUSEWHEEL = "core_mousewheel"
        WINDOWRESIZED = "core_windowresized"
        TEXTINPUT = "core_textinput"

    @dataclass
    class FakeEvent:
        type: object
        key: object = None
        x: object = None
        y: object = None
        dx: object = None
        dy: object = None
        button: object = None
        wheel: object = None
        size: object = None
        text: object = None
        scancode: object = None
        mod: object = None
        repeat: object = None

    fake_core.Backend = FakeBackend
    fake_core.Event = FakeEvent
    fake_core.EventType = FakeCoreEventType

    sys.modules["mini_arcade_core"] = fake_core

    # --- Fake native extension: mini_arcade_native_backend._native -------------
    fake_native = types.ModuleType("mini_arcade_native_backend._native")

    class FakeNativeEventType:
        Unknown = "native_unknown"
        Quit = "native_quit"
        KeyDown = "native_keydown"
        KeyUp = "native_keyup"
        MouseMotion = "native_mousemotion"
        MouseButtonDown = "native_mousebuttondown"
        MouseButtonUp = "native_mousebuttonup"
        MouseWheel = "native_mousewheel"
        WindowResized = "native_windowresized"
        TextInput = "native_textinput"

    class FakeEngine:
        def __init__(self):
            self.init_args = None
            self.frames = []
            self.rects = []
            self._events_to_return = []

        def init(self, width, height, title):
            self.init_args = (width, height, title)

        def poll_events(self):
            return list(self._events_to_return)

        def begin_frame(self):
            self.frames.append("begin")

        def end_frame(self):
            self.frames.append("end")

        def draw_rect(self, x, y, w, h, r, g, b):
            self.rects.append((x, y, w, h, r, g, b))

    fake_native.EventType = FakeNativeEventType
    fake_native.Engine = FakeEngine

    # Register the fake native module under the expected name
    sys.modules["mini_arcade_native_backend._native"] = fake_native

    return fake_core, fake_native


def import_backend_package(
    monkeypatch, *, platform="linux", vcpkg_root=None, sdl_dir_exists=False
):
    """
    Helper to import mini_arcade_native_backend with controlled platform/env.
    Returns (package_module, fake_core_module, fake_native_module, added_paths).
    """
    fake_core, fake_native = setup_fake_core_and_native(monkeypatch)

    # Control sys.platform
    monkeypatch.setattr(sys, "platform", platform)

    # Control VCPKG_ROOT
    if vcpkg_root is None:
        monkeypatch.delenv("VCPKG_ROOT", raising=False)
    else:
        monkeypatch.setenv("VCPKG_ROOT", vcpkg_root)

    # Track calls to os.add_dll_directory (may not exist on non-Windows)
    added_paths = []

    def fake_add_dll_directory(path):
        added_paths.append(path)

    monkeypatch.setattr(
        os, "add_dll_directory", fake_add_dll_directory, raising=False
    )

    # Control os.path.isdir for the SDL bin path check
    real_isdir = os.path.isdir

    def fake_isdir(path):
        if sdl_dir_exists:
            return True
        return real_isdir(path)

    monkeypatch.setattr(os.path, "isdir", fake_isdir)

    # Force a fresh import of the package so the top-level code re-runs
    sys.modules.pop("mini_arcade_native_backend", None)
    pkg = importlib.import_module("mini_arcade_native_backend")

    return pkg, fake_core, fake_native, added_paths


# --------------------------------------------------------------------------- #
#  DLL path / Windows bootstrap tests
# --------------------------------------------------------------------------- #


def test_non_windows_does_not_add_dll_directory(monkeypatch):
    pkg, fake_core, fake_native, added_paths = import_backend_package(
        monkeypatch,
        platform="linux",
        vcpkg_root=None,
        sdl_dir_exists=False,
    )

    assert added_paths == []


def test_windows_without_vcpkg_root_does_not_add_dll_directory(monkeypatch):
    pkg, fake_core, fake_native, added_paths = import_backend_package(
        monkeypatch,
        platform="win32",
        vcpkg_root=None,
        sdl_dir_exists=True,
    )

    assert added_paths == []


def test_windows_with_vcpkg_root_and_existing_sdl_dir_adds_dll_directory(
    monkeypatch,
):
    vcpkg_root = r"C:\vcpkg"

    pkg, fake_core, fake_native, added_paths = import_backend_package(
        monkeypatch,
        platform="win32",
        vcpkg_root=vcpkg_root,
        sdl_dir_exists=True,
    )

    expected_sdl_bin = os.path.join(
        vcpkg_root, "installed", "x64-windows", "bin"
    )
    assert expected_sdl_bin in added_paths


# --------------------------------------------------------------------------- #
#  NativeBackend behaviour tests
# --------------------------------------------------------------------------- #


@pytest.fixture
def backend_module(monkeypatch):
    """
    Import the package on a non-Windows platform and return:
    (pkg, fake_core, fake_native)
    """
    pkg, fake_core, fake_native, _ = import_backend_package(
        monkeypatch,
        platform="linux",
        vcpkg_root=None,
        sdl_dir_exists=False,
    )
    return pkg, fake_core, fake_native


def test_exports_nativebackend_and_native(backend_module):
    pkg, fake_core, fake_native = backend_module
    assert "NativeBackend" in pkg.__all__
    assert "native" in pkg.__all__


def test_nativebackend_init_calls_engine_init(backend_module):
    pkg, fake_core, fake_native = backend_module

    backend = pkg.NativeBackend()
    backend.init(800, 600, "Test Window")

    engine = backend._engine
    assert engine.init_args == (800, 600, "Test Window")


def test_nativebackend_begin_end_frame_delegate_to_engine(backend_module):
    pkg, fake_core, fake_native = backend_module

    backend = pkg.NativeBackend()
    backend.begin_frame()
    backend.end_frame()

    assert backend._engine.frames == ["begin", "end"]


def test_nativebackend_draw_rect_delegates_to_engine(backend_module):
    pkg, fake_core, fake_native = backend_module

    backend = pkg.NativeBackend()
    backend.draw_rect(10, 20, 30, 40, color=(255, 0, 0))

    assert backend._engine.rects == [(10, 20, 30, 40, 255, 0, 0)]


def test_poll_events_maps_native_events_to_core_events_and_keys(
    backend_module,
):
    pkg, fake_core, fake_native = backend_module
    backend = pkg.NativeBackend()

    @dataclass
    class FakeNativeEvent:
        type: object
        key: int = 0
        x: int = 0
        y: int = 0
        dx: int = 0
        dy: int = 0
        button: int = 0
        wheel_x: int = 0
        wheel_y: int = 0
        width: int = 0
        height: int = 0
        text: str = ""
        scancode: int = 0
        mod: int = 0
        repeat: int = 0

    engine = backend._engine
    engine._events_to_return = [
        FakeNativeEvent(fake_native.EventType.Quit),  # -> QUIT
        FakeNativeEvent(
            fake_native.EventType.KeyDown, key=32
        ),  # -> KEYDOWN, key=32
        FakeNativeEvent(
            fake_native.EventType.MouseMotion, x=10, y=20, dx=1, dy=-2
        ),
        FakeNativeEvent(
            fake_native.EventType.MouseButtonDown, x=5, y=6, button=1
        ),
        FakeNativeEvent(
            fake_native.EventType.MouseWheel, wheel_x=0, wheel_y=-1
        ),
        FakeNativeEvent(
            fake_native.EventType.WindowResized, width=800, height=600
        ),
        FakeNativeEvent(fake_native.EventType.TextInput, text="á"),
        FakeNativeEvent("something_unknown", key=10),  # -> UNKNOWN, key=10
    ]

    events = backend.poll_events()
    assert len(events) == 8

    # Quit: key 0 -> None
    assert events[0].type == fake_core.EventType.QUIT
    assert events[0].key is None

    # KeyDown: key passes through
    assert events[1].type == fake_core.EventType.KEYDOWN
    assert events[1].key == 32

    # MouseMotion: x/y/dx/dy mapped (0 becomes None; here non-zero)
    assert events[2].type == fake_core.EventType.MOUSEMOTION
    assert events[2].x == 10
    assert events[2].y == 20
    assert events[2].dx == 1
    assert events[2].dy == -2

    # MouseButtonDown
    assert events[3].type == fake_core.EventType.MOUSEBUTTONDOWN
    assert events[3].x == 5
    assert events[3].y == 6
    assert events[3].button == 1

    # MouseWheel -> wheel tuple
    assert events[4].type == fake_core.EventType.MOUSEWHEEL
    assert events[4].wheel == (0, -1)

    # WindowResized -> size tuple
    assert events[5].type == fake_core.EventType.WINDOWRESIZED
    assert events[5].size == (800, 600)

    # TextInput -> text
    assert events[6].type == fake_core.EventType.TEXTINPUT
    assert events[6].text == "á"

    # Unknown
    assert events[7].type == fake_core.EventType.UNKNOWN
    assert events[7].key == 10
