# -*- coding: utf-8 -*-
"""Virtual Xbox 360 gamepad output via ViGEm Bus Driver + vgamepad library.

Requirements (one-time install):
  1. ViGEm Bus Driver: https://github.com/nefarius/ViGEmBus/releases
  2. pip install vgamepad
"""
import time

try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except (ImportError, Exception):
    vg = None
    VGAMEPAD_AVAILABLE = False


# Direction name → Xbox 360 DPAD button constant name
_DIR_TO_DPAD = {
    "up":    "XUSB_GAMEPAD_DPAD_UP",
    "down":  "XUSB_GAMEPAD_DPAD_DOWN",
    "left":  "XUSB_GAMEPAD_DPAD_LEFT",
    "right": "XUSB_GAMEPAD_DPAD_RIGHT",
}

# Human-readable button name → Xbox 360 constant name
XBOX_BUTTONS = {
    "A":  "XUSB_GAMEPAD_A",
    "B":  "XUSB_GAMEPAD_B",
    "X":  "XUSB_GAMEPAD_X",
    "Y":  "XUSB_GAMEPAD_Y",
    "LB": "XUSB_GAMEPAD_LEFT_SHOULDER",
    "RB": "XUSB_GAMEPAD_RIGHT_SHOULDER",
    "LT": None,   # trigger — handled separately via left_trigger()
    "RT": None,   # trigger — handled separately via right_trigger()
    "DPAD_UP":    "XUSB_GAMEPAD_DPAD_UP",
    "DPAD_DOWN":  "XUSB_GAMEPAD_DPAD_DOWN",
    "DPAD_LEFT":  "XUSB_GAMEPAD_DPAD_LEFT",
    "DPAD_RIGHT": "XUSB_GAMEPAD_DPAD_RIGHT",
}

# Default attack name → Xbox button (standard 6-button SF layout)
DEFAULT_ATTACK_MAP = {
    # SF-style
    "LP": "A",  "MP": "B",  "HP": "X",
    "LK": "Y",  "MK": "LB", "HK": "RB",
    # SNK 4-button
    "A":  "A",  "B":  "B",  "C":  "X",  "D":  "Y",
    # Generic
    "P1": "A",  "P2": "B",  "P3": "X",
    "K1": "Y",  "K2": "LB", "K3": "RB",
}


def _btn_const(name: str):
    """Return the vg.XUSB_BUTTON constant for a button name, or None."""
    if not vg:
        return None
    attr = XBOX_BUTTONS.get(name.upper())
    if attr:
        return getattr(vg.XUSB_BUTTON, attr, None)
    return None


class VirtualGamepad:
    """Thin wrapper around vgamepad.VX360Gamepad for use in MacroExecutor."""

    def __init__(self):
        self.available = False
        self.error: str = ""
        self._pad = None
        if VGAMEPAD_AVAILABLE:
            try:
                self._pad = vg.VX360Gamepad()
                self._pad.update()
                self.available = True
            except Exception as e:
                self._pad = None
                self.error = str(e)
        else:
            self.error = "vgamepad no instalado (pip install vgamepad)"

    # ── Low-level helpers ──────────────────────────────────────────────────

    def _press(self, const):
        self._pad.press_button(button=const)

    def _release(self, const):
        self._pad.release_button(button=const)

    def _flush(self):
        self._pad.update()

    # ── High-level API used by executor ───────────────────────────────────

    def hold_buttons(self, btn_names: list):
        """Hold a set of buttons (does NOT release). Call release_buttons() after."""
        if not self._pad:
            return
        for name in btn_names:
            c = _btn_const(name)
            if c:
                self._press(c)
        self._flush()

    def release_buttons(self, btn_names: list):
        """Release previously held buttons."""
        if not self._pad:
            return
        for name in reversed(btn_names):
            c = _btn_const(name)
            if c:
                self._release(c)
        self._flush()

    def tap_buttons(self, btn_names: list, hold_sec: float = 0.05):
        """Press and release buttons with a short hold."""
        if not self._pad or not btn_names:
            return
        self.hold_buttons(btn_names)
        if hold_sec > 0:
            time.sleep(hold_sec)
        self.release_buttons(btn_names)

    def reset(self):
        if not self._pad:
            return
        self._pad.reset()
        self._pad.update()

    # ── Direction helpers (map direction names → dpad buttons) ─────────────

    @staticmethod
    def dir_names_to_dpad(dir_names: list) -> list:
        """Convert direction names ('up','left',...) to Xbox dpad button names."""
        result = []
        for d in dir_names:
            dpad = _DIR_TO_DPAD.get(d)
            if dpad:
                result.append(dpad)
        return result
