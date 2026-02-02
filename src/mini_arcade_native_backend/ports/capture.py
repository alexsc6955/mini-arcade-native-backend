"""
Capture port implementation for Mini Arcade Native Backend.
Provides functionality to capture screenshots in BMP format.
"""

from __future__ import annotations

# Justification: native is a compiled extension module.
# pylint: disable=no-name-in-module
from mini_arcade_native_backend import _native as native  # type: ignore


class CapturePort:
    """
    Capture port for the Mini Arcade native backend.

    :param native_backend: The native backend instance.
    :type native_backend: native.Backend
    """

    def __init__(self, native_backend: native.Backend):
        self._b = native_backend

    def bmp(self, path: str) -> bool:
        """
        Capture the current screen and save it as a BMP file.

        :param path: The file path to save the BMP screenshot.
        :type path: str
        :return: True if the screenshot was successfully saved, False otherwise.
        :rtype: bool
        """
        return bool(self._b.capture_bmp(str(path)))
