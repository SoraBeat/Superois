# -*- coding: utf-8 -*-
import threading
import time
import ctypes
from typing import Callable, Optional, Dict, List
from core.combo import Combo
from core.game import NUMPAD_TO_DIRS
from core.input_manager import keysym_to_pyautogui
from core.virtual_gamepad import VirtualGamepad, DEFAULT_ATTACK_MAP

# Numpad mirror map: swaps left ↔ right, keeps up/down/neutral the same
MIRROR_MAP = {
    "4": "6", "6": "4",
    "7": "9", "9": "7",
    "1": "3", "3": "1",
}

# ── Keyboard input library ─────────────────────────────────────────────────────
try:
    import core.direct_input as _inp
    AVAILABLE = True
    INPUT_BACKEND = "direct_input"
except ImportError:
    _inp = None
    AVAILABLE = False
    INPUT_BACKEND = "none"


def _binding_to_key(binding: Optional[Dict]) -> Optional[str]:
    if not binding or binding.get("type") != "keyboard":
        return None
    raw = keysym_to_pyautogui(binding.get("key", ""))
    return raw if raw else None


def _press_kb(key: str, hold_time: float = 0.05):
    if not _inp: return
    _inp.key_down(key)
    time.sleep(hold_time)
    _inp.key_up(key)


def _press_simultaneous_kb(keys: List[str], hold_extra: float = 0.05):
    if not _inp: return
    for k in keys:
        _inp.key_down(k)
    if hold_extra > 0:
        time.sleep(hold_extra)
    for k in reversed(keys):
        _inp.key_up(k)


# ── Executor ───────────────────────────────────────────────────────────────────

class MacroExecutor:
    def __init__(self):
        self.available = AVAILABLE
        self.backend = INPUT_BACKEND
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        self._stop_event.set()

    def execute(
        self,
        combo: Combo,
        dir_bindings: Dict,
        attack_bindings: Dict,
        pre_delay: float = 3.0,
        step_delay: float = 0.0,
        mirror: bool = False,
        game_hwnd: Optional[int] = None,
        vpad: Optional[VirtualGamepad] = None,
        vpad_attack_map: Optional[Dict[str, str]] = None,
        on_countdown: Optional[Callable[[int], None]] = None,
        on_start: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        vpad            — VirtualGamepad instance (if None, uses keyboard)
        vpad_attack_map — {attack_name: xbox_button_name} e.g. {"LP": "A", "MP": "B"}
                          Defaults to DEFAULT_ATTACK_MAP if not provided.
        """
        if not self.available and vpad is None:
            if on_error:
                on_error(
                    "Error al inicializar la inyección de teclado (core.direct_input)."
                )
            return
        if self.is_running():
            return

        self._stop_event.clear()
        attack_map = vpad_attack_map or DEFAULT_ATTACK_MAP

        def run():
            try:
                for i in range(int(pre_delay), 0, -1):
                    if self._stop_event.is_set():
                        return
                    if on_countdown:
                        on_countdown(i)
                    time.sleep(1)

                if on_start:
                    on_start()

                use_vpad = vpad is not None and vpad.available
                self._run_combo(combo, dir_bindings, attack_bindings,
                                step_delay, mirror, use_vpad, vpad, attack_map)

                if on_complete:
                    on_complete()
            except Exception as e:
                if on_error:
                    on_error(str(e))

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def _run_combo(
        self,
        combo: Combo,
        dir_bindings: Dict,
        attack_bindings: Dict,
        step_delay: float,
        mirror: bool,
        use_vpad: bool,
        vpad: Optional[VirtualGamepad],
        attack_map: Dict[str, str],
    ):
        for step in combo.steps:
            if self._stop_event.is_set():
                break

            # Mirror mode: swap left ↔ right
            direction = MIRROR_MAP.get(step.direction, step.direction) if mirror else step.direction

            # ── Resolve directions ─────────────────────────────────────────
            dir_names = NUMPAD_TO_DIRS.get(direction, [])  # e.g. ["up", "left"]

            # ── Resolve attacks ────────────────────────────────────────────
            atk_names = step.attacks  # e.g. ["LP", "MK"]

            # ── Execute via virtual gamepad ────────────────────────────────
            if use_vpad:
                dpad_btns = VirtualGamepad.dir_names_to_dpad(dir_names)
                atk_btns  = [attack_map.get(a) for a in atk_names
                             if attack_map.get(a)]
                all_btns  = dpad_btns + atk_btns

                if not all_btns:
                    if step_delay > 0:
                        time.sleep(step_delay)
                    continue

                hold_sec = max(step.delay_ms / 1000.0, 0.05) if step.hold else 0.05

                if step.hold:
                    vpad.hold_buttons(all_btns)
                    time.sleep(hold_sec)
                    vpad.release_buttons(all_btns)
                else:
                    vpad.tap_buttons(all_btns, hold_sec=hold_sec)

                extra = step.delay_ms / 1000.0 if not step.hold else 0.0
                total_delay = step_delay + extra
                if total_delay > 0:
                    time.sleep(total_delay)

            # ── Execute via keyboard ───────────────────────────────────────
            else:
                if not _inp:
                    continue
                dir_keys = [_binding_to_key(dir_bindings.get(d)) for d in dir_names]
                dir_keys = [k for k in dir_keys if k]

                atk_keys = [_binding_to_key(attack_bindings.get(a)) for a in atk_names]
                atk_keys = [k for k in atk_keys if k]

                all_keys = dir_keys + atk_keys

                if not all_keys:
                    if step_delay > 0:
                        time.sleep(step_delay)
                    continue

                if step.hold:
                    for k in all_keys:
                        _inp.key_down(k)
                    hold_time = max(step.delay_ms / 1000.0, 0.05)
                    time.sleep(hold_time)
                    for k in reversed(all_keys):
                        _inp.key_up(k)
                elif len(all_keys) == 1:
                    _press_kb(all_keys[0])
                else:
                    _press_simultaneous_kb(all_keys)

                extra = step.delay_ms / 1000.0 if not step.hold else 0.0
                total_delay = step_delay + extra
                if total_delay > 0:
                    time.sleep(total_delay)
