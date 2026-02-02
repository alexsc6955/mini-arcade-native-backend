"""
Configuration and utility functions for the mini arcade native backend.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from mini_arcade_core.backend.types import (  # pyright: ignore[reportMissingImports]
    Alpha,
    Color,
    ColorRGBA,
)


@dataclass(frozen=True)
class WindowSettings:
    """
    Configuration for a game window (not implemented).

    :ivar width (int): Width of the window in pixels.
    :ivar height (int): Height of the window in pixels.
    :ivar title (str): Title of the window.
    :ivar resizable (bool): Whether the window is resizable. Default is True.
    :ivar high_dpi (bool): Whether to enable high-DPI support. Default is True.
    """

    width: int
    height: int
    title: str
    resizable: bool = True
    high_dpi: bool = True


class RenderAPI(Enum):
    """
    Enumeration of supported rendering APIs.
    """

    SDL2 = "SDL2"


@dataclass(frozen=True)
class RendererSettings:
    """
    Configuration for the renderer (not implemented).

    :ivar api (RenderAPI): Rendering API to use.
    :ivar background_color (Color): Background color as (r,g,b, optional alpha).
    """

    api: RenderAPI = field(default=RenderAPI.SDL2)
    background_color: Color = (0, 0, 0)

    def rgba(self) -> tuple[int, int, int, int]:
        """
        Get the background color in RGBA format.

        :return: Background color as (r,g,b,a) with alpha as 0-255 integer.
        :rtype: tuple[int, int, int, int]
        """
        return rgba(self.background_color)


@dataclass(frozen=True)
class FontSettings:
    """
    Configuration for font rendering (not implemented).

    :ivar name (str): Name of the font.
    :ivar font_path (Optional[str]): Path to the font file.
    :ivar font_size (int): Default font size.
    """

    name: str = "default"
    path: Optional[str] = None
    size: int = 24


@dataclass(frozen=True)
class AudioSettings:
    """
    Configuration for audio settings (not implemented).

    :ivar enable (bool): Whether to enable audio support.
    :ivar sounds (Optional[dict[str, str]]): Mapping of sound names to file paths.
    """

    enable: bool = False
    sounds: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class BackendSettings:
    """
    Settings for configuring the native backend.

    :ivar window (WindowSettings): Window settings for the backend.
    :ivar renderer (RendererSettings): Renderer settings for the backend.
    :ivar font (FontSettings): Font settings for text rendering.
    :ivar audio (AudioSettings): Audio settings for the backend.
    """

    window: WindowSettings = field(
        default_factory=lambda: WindowSettings(
            width=800,
            height=600,
            title="Mini Arcade",
            resizable=True,
            high_dpi=True,
        )
    )
    renderer: RendererSettings = field(default_factory=RendererSettings)
    fonts: list[FontSettings] = field(default_factory=lambda: [FontSettings()])
    audio: AudioSettings = field(default_factory=AudioSettings)

    def to_dict(self) -> dict:
        """
        Convert the BackendSettings to a dictionary.

        :return: Dictionary representation of the settings.
        :rtype: dict
        """
        return asdict(self)


def alpha_to_u8(alpha: Alpha | None) -> int:
    """
    Convert an alpha value to an 8-bit integer (0-255).

    :param alpha: Alpha value as float [0.0, 1.0] or int [0, 255], or None for opaque.
    :type alpha: Optional[Union[float, int]]
    :return: Alpha as an integer in the range 0-255.
    :rtype: int
    :raises TypeError: If alpha is a bool.
    :raises ValueError: If alpha is out of range.
    """
    if alpha is None:
        return 255
    if isinstance(alpha, bool):
        raise TypeError("alpha must be a float in [0,1], not bool")
    if isinstance(alpha, int):
        if not 0 <= alpha <= 255:
            raise ValueError(f"int alpha must be in [0, 255], got {alpha!r}")
        return alpha

    a = float(alpha)
    if not 0.0 <= a <= 1.0:
        raise ValueError(f"float alpha must be in [0, 1], got {alpha!r}")
    return int(round(a * 255))


def rgba(color: Color) -> ColorRGBA:
    """
    Convert a color tuple to RGBA format.

    :param color: Color as (r,g,b) or (r,g,b,a).
    :type color: Color
    :return: Color as (r,g,b,a) with alpha as 0-255 integer.
    :rtype: ColorRGBA
    """
    if len(color) == 3:
        r, g, b = color
        return int(r), int(g), int(b), 255
    if len(color) == 4:
        r, g, b, a = color
        return int(r), int(g), int(b), alpha_to_u8(a)
    raise ValueError(f"Color must be (r,g,b) or (r,g,b,a), got {color!r}")


def validate_file_exists(path: str) -> str:
    """
    Validate that a file exists at the given path.

    :param path: Path to the file.
    :type path: str
    :return: The original path if the file exists.
    :rtype: str
    :raises FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return str(p)
