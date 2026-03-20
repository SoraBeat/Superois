# -*- coding: utf-8 -*-
"""Input management: gamepad detection via pygame + global keyboard hotkeys."""
import threading
import time
from typing import Optional, Callable, Dict, List, Tuple

try:
    import pygame
    _PYGAME = True
except ImportError:
    _PYGAME = False

try:
    import keyboard as _kb_lib
    _KEYBOARD = True
except ImportError:
    _KEYBOARD = False


# Map tkinter keysyms → pyautogui/keyboard key names
KEYSYM_MAP = {
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Return": "enter", "space": "space", "BackSpace": "backspace",
    "Escape": "escape", "Tab": "tab",
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4",
    "F5": "f5", "F6": "f6", "F7": "f7", "F8": "f8",
    "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
    "Prior": "pageup", "Next": "pagedown",
    "Home": "home", "End": "end", "Insert": "insert", "Delete": "delete",
    "KP_0": "num0", "KP_1": "num1", "KP_2": "num2", "KP_3": "num3",
    "KP_4": "num4", "KP_5": "num5", "KP_6": "num6", "KP_7": "num7",
    "KP_8": "num8", "KP_9": "num9",
    "Control_L": "ctrl", "Control_R": "ctrl",
    "Alt_L": "alt", "Alt_R": "alt",
    "Shift_L": "shift", "Shift_R": "shift",
}

# These keysyms are modifier-only, ignore during capture
IGNORE_KEYSYMS = {
    "Shift_L", "Shift_R", "Control_L", "Control_R",
    "Alt_L", "Alt_R", "Super_L", "Super_R", "Caps_Lock",
}


def keysym_to_pyautogui(keysym: str) -> str:
    """Convert a tkinter keysym to a pyautogui-compatible key name."""
    return KEYSYM_MAP.get(keysym, keysym.lower())


def format_binding(binding: Optional[Dict]) -> str:
    """Return a human-readable string for a binding dict."""
    if not binding:
        return "— sin asignar —"
    t = binding.get("type", "")
    if t == "keyboard":
        key = binding.get("key", "?")
        return f"Tecl: {key.upper()}"
    if t == "gamepad":
        dev = binding.get("device", 0)
        if "button" in binding:
            return f"Pad {dev}: Botón {binding['button']}"
        if "axis" in binding:
            d = "+" if binding.get("dir", 1) > 0 else "-"
            return f"Pad {dev}: Eje {binding['axis']}{d}"
        if "hat" in binding:
            return f"Pad {dev}: Hat {binding['hat']}"
    return "?"


class InputManager:
    """Manages gamepad polling and global keyboard hotkeys."""

    AXIS_THRESHOLD = 0.5

    def __init__(self):
        self._pygame_ready = False
        self._joysticks: List = []
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False
        self._macro_trigger: Optional[Dict] = None
        self._on_trigger: Optional[Callable] = None
        self._combo_hotkeys: Dict[str, Dict] = {}          # combo_id -> binding
        self._on_combo_trigger: Optional[Callable] = None  # called with combo_id
        self._kb_registered = False

    # ── PYGAME INIT ───────────────────────────────────────────────────────────

    def init_pygame(self) -> bool:
        if _PYGAME and not self._pygame_ready:
            try:
                pygame.init()
                pygame.joystick.init()
                self._pygame_ready = True
            except Exception:
                pass
        return self._pygame_ready

    def refresh_joysticks(self):
        if not self.init_pygame():
            return
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            self._joysticks = []
            for i in range(pygame.joystick.get_count()):
                j = pygame.joystick.Joystick(i)
                j.init()
                self._joysticks.append(j)
        except Exception:
            pass

    def get_joystick_names(self) -> List[Tuple[int, str]]:
        return [(i, j.get_name()) for i, j in enumerate(self._joysticks)]

    def has_gamepad(self) -> bool:
        self.refresh_joysticks()
        return bool(self._joysticks)

    @property
    def pygame_available(self) -> bool:
        return _PYGAME

    @property
    def keyboard_lib_available(self) -> bool:
        return _KEYBOARD

    # ── MACRO TRIGGER ─────────────────────────────────────────────────────────

    def set_macro_trigger(self, binding: Optional[Dict], callback: Callable):
        """Register the global macro hotkey/button."""
        self._macro_trigger = binding
        self._on_trigger = callback
        self._update_all_kb_hotkeys()
        if not self._running:
            self.start_polling()

    def register_combo_hotkeys(
        self,
        hotkey_map: Dict,               # {combo_id: binding_dict}
        on_trigger: Callable,           # called with combo_id
    ):
        """Register per-combo hotkeys. Replaces any previous registration."""
        self._combo_hotkeys = hotkey_map
        self._on_combo_trigger = on_trigger
        self._update_all_kb_hotkeys()
        if not self._running:
            self.start_polling()

    def _update_all_kb_hotkeys(self):
        """Re-register all keyboard hotkeys (macro trigger + all combo hotkeys)."""
        if not _KEYBOARD:
            return
        # Unhook everything first
        try:
            _kb_lib.unhook_all_hotkeys()
        except Exception:
            pass
        self._kb_registered = False

        # Global macro trigger
        t = self._macro_trigger
        if t and t.get("type") == "keyboard" and self._on_trigger:
            pykey = keysym_to_pyautogui(t.get("key", ""))
            if pykey:
                try:
                    _kb_lib.add_hotkey(pykey, self._on_trigger, suppress=False)
                    self._kb_registered = True
                except Exception:
                    pass

        # Per-combo hotkeys
        for combo_id, binding in self._combo_hotkeys.items():
            if not binding or binding.get("type") != "keyboard":
                continue
            pykey = keysym_to_pyautogui(binding.get("key", ""))
            if pykey and self._on_combo_trigger:
                cid = combo_id
                try:
                    _kb_lib.add_hotkey(
                        pykey,
                        lambda c=cid: self._on_combo_trigger(c),
                        suppress=False,
                    )
                except Exception:
                    pass

    # kept for back-compat
    def _update_kb_hotkey(self):
        self._update_all_kb_hotkeys()

    def start_polling(self):
        if self._running:
            return
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop_polling(self):
        self._running = False
        if self._kb_registered and _KEYBOARD:
            try:
                _kb_lib.unhook_all_hotkeys()
            except Exception:
                pass

    def _poll_loop(self):
        self.init_pygame()
        while self._running:
            if self._pygame_ready:
                try:
                    pygame.event.pump()
                    events = pygame.event.get()
                    for event in events:
                        # Global macro trigger (gamepad)
                        t = self._macro_trigger
                        if t and t.get("type") == "gamepad":
                            if self._matches_gamepad_event(event, t) and self._on_trigger:
                                self._on_trigger()
                        # Per-combo hotkeys (gamepad)
                        for combo_id, binding in list(self._combo_hotkeys.items()):
                            if binding and binding.get("type") == "gamepad":
                                if self._matches_gamepad_event(event, binding):
                                    if self._on_combo_trigger:
                                        self._on_combo_trigger(combo_id)
                except Exception:
                    pass
            time.sleep(0.016)

    def _matches_gamepad_event(self, event, binding: Dict) -> bool:
        if not _PYGAME:
            return False
        dev = binding.get("device", 0)
        if "button" in binding:
            return (event.type == pygame.JOYBUTTONDOWN and
                    event.joy == dev and event.button == binding["button"])
        if "axis" in binding:
            if event.type != pygame.JOYAXISMOTION:
                return False
            if event.joy != dev or event.axis != binding["axis"]:
                return False
            d = binding.get("dir", 1)
            v = event.value
            return (d > 0 and v > self.AXIS_THRESHOLD) or (d < 0 and v < -self.AXIS_THRESHOLD)
        return False

    # ── CAPTURE (used by settings dialog) ────────────────────────────────────

    def poll_for_capture(self) -> Optional[Dict]:
        """Non-blocking: returns first gamepad event detected, or None."""
        if not self._pygame_ready:
            return None
        try:
            pygame.event.pump()
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    return {"type": "gamepad", "device": event.joy, "button": event.button}
                if event.type == pygame.JOYAXISMOTION and abs(event.value) > self.AXIS_THRESHOLD:
                    d = 1 if event.value > 0 else -1
                    return {"type": "gamepad", "device": event.joy,
                            "axis": event.axis, "dir": d}
                if event.type == pygame.JOYHATMOTION and event.value != (0, 0):
                    return {"type": "gamepad", "device": event.joy,
                            "hat": str(event.value)}
        except Exception:
            pass
        return None
