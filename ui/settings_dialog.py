# -*- coding: utf-8 -*-
"""Settings Dialog — key mappings, gamepad config, macro timing."""
import customtkinter as ctk
from typing import Optional, Dict, Callable

from core.input_manager import InputManager, format_binding, IGNORE_KEYSYMS

# ── Theme (mirror app.py) ─────────────────────────────────────────────────────
BG      = "#0A0A0F"
SURFACE = "#12121A"
CARD    = "#1C1C2E"
BORDER  = "#2A2A40"
PRIMARY = "#FF4500"
PHOVER  = "#CC3300"
CYAN    = "#00D4FF"
GOLD    = "#FFD700"
GREEN   = "#00C853"
AMBER   = "#FF9800"
RED     = "#FF1744"
TEXT    = "#F0F0FF"
MUTED   = "#8888AA"

FONT_HEADER = ("Consolas", 13, "bold")
FONT_BODY   = ("Consolas", 11)
FONT_SMALL  = ("Consolas", 9)


def _default_dir_bindings() -> Dict:
    return {
        "up":    {"type": "keyboard", "key": "Up"},
        "down":  {"type": "keyboard", "key": "Down"},
        "left":  {"type": "keyboard", "key": "Left"},
        "right": {"type": "keyboard", "key": "Right"},
    }


class SettingsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        game,
        settings: dict,
        input_mgr: InputManager,
        on_save: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.title("Configuración — SupeRois")
        self.geometry("720x600")
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self.grab_set()
        self.focus_set()

        self.game = game
        self.settings = settings
        self.input_mgr = input_mgr
        self.on_save = on_save

        # Work on copies of the relevant settings
        game_id = game.id if game else "default"
        stored = settings.get("key_mappings", {}).get(game_id, {})

        self._dirs: Dict = dict(stored.get("dirs", _default_dir_bindings()))
        self._attacks: Dict = {}
        if game:
            default_atk = {
                btn: {"type": "keyboard", "key": k}
                for btn, k in game.default_keys.items()
            }
            self._attacks = dict(stored.get("attacks", default_atk))

        self._macro_trigger: Dict = dict(
            settings.get("macro_trigger", {"type": "keyboard", "key": "F8"})
        )
        self._exec_delay: float = settings.get("exec_delay", 0.05)
        self._pre_delay: int   = int(settings.get("pre_delay", 3))

        self._capturing = None  # (section, action_id, label_widget)

        self._build()
        self.input_mgr.init_pygame()
        self.input_mgr.refresh_joysticks()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    # ── BUILD ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="⚙  CONFIGURACIÓN", font=FONT_HEADER,
                     text_color=GOLD, pady=12, padx=20).pack(side="left")
        game_name = self.game.name if self.game else "—"
        ctk.CTkLabel(hdr, text=f"Juego activo: {game_name}",
                     font=FONT_SMALL, text_color=MUTED, padx=15).pack(side="right")

        # Tabs
        self.tabs = ctk.CTkTabview(
            self, fg_color=SURFACE,
            segmented_button_fg_color=CARD,
            segmented_button_selected_color=PRIMARY,
            segmented_button_selected_hover_color=PHOVER,
            segmented_button_unselected_color=CARD,
            segmented_button_unselected_hover_color=BORDER,
        )
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        t_dirs  = self.tabs.add("Movimiento")
        t_atk   = self.tabs.add("Ataques")
        t_macro = self.tabs.add("Macro")
        t_pads  = self.tabs.add("Gamepads")

        self._build_dirs_tab(t_dirs)
        self._build_attacks_tab(t_atk)
        self._build_macro_tab(t_macro)
        self._build_gamepads_tab(t_pads)

        # Bottom bar
        bar = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0)
        bar.pack(fill="x", side="bottom")

        self.status_lbl = ctk.CTkLabel(bar, text="", font=FONT_SMALL, text_color=MUTED)
        self.status_lbl.pack(side="left", padx=15, pady=10)

        ctk.CTkButton(bar, text="Cancelar", font=FONT_BODY, width=100,
                      fg_color=SURFACE, hover_color=BORDER,
                      command=self._cancel).pack(side="right", padx=8, pady=10)
        ctk.CTkButton(bar, text="Guardar", font=FONT_BODY, width=120,
                      fg_color=GREEN, hover_color="#009624",
                      command=self._save).pack(side="right", pady=10)

    # ── TABS ──────────────────────────────────────────────────────────────────

    def _build_dirs_tab(self, parent):
        ctk.CTkLabel(
            parent,
            text="Configura las teclas/botones de dirección para este juego.\n"
                 "Los diagonales se obtienen combinando dos direcciones simultáneamente.",
            font=FONT_SMALL, text_color=MUTED, justify="left",
        ).pack(anchor="w", padx=12, pady=(8, 10))

        directions = [
            ("up",    "Arriba      ↑"),
            ("down",  "Abajo       ↓"),
            ("left",  "Izquierda   ←"),
            ("right", "Derecha     →"),
        ]
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4)
        for action_id, label in directions:
            self._make_row(scroll, "dirs", action_id, label, self._dirs.get(action_id))

    def _build_attacks_tab(self, parent):
        ctk.CTkLabel(
            parent,
            text="Configura las teclas/botones de ataque para este juego.",
            font=FONT_SMALL, text_color=MUTED,
        ).pack(anchor="w", padx=12, pady=(8, 10))

        if not self.game:
            ctk.CTkLabel(parent, text="Sin juego seleccionado.", font=FONT_BODY,
                         text_color=MUTED).pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4)
        for btn_name in self.game.buttons:
            self._make_row(scroll, "attacks", btn_name, btn_name,
                           self._attacks.get(btn_name))

    def _build_macro_tab(self, parent):
        # Trigger binding
        trig = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=8)
        trig.pack(fill="x", padx=10, pady=(12, 6))
        trig.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(trig, text="Hotkey — ejecutar macro", font=FONT_BODY,
                     text_color=TEXT, width=220, anchor="w"
                     ).grid(row=0, column=0, padx=12, pady=10)

        self._trig_lbl = ctk.CTkLabel(trig, text=format_binding(self._macro_trigger),
                                       font=FONT_BODY, text_color=CYAN, anchor="w")
        self._trig_lbl.grid(row=0, column=1, sticky="w", padx=6)

        ctk.CTkButton(trig, text="Capturar", width=80, font=FONT_SMALL,
                      fg_color=PRIMARY, hover_color=PHOVER, corner_radius=4,
                      command=lambda: self._start_capture("trigger", "macro_trigger",
                                                          self._trig_lbl)
                      ).grid(row=0, column=2, padx=4, pady=8)
        ctk.CTkButton(trig, text="Limpiar", width=70, font=FONT_SMALL,
                      fg_color=SURFACE, hover_color=BORDER, corner_radius=4,
                      command=self._clear_trigger
                      ).grid(row=0, column=3, padx=(0, 8), pady=8)

        ctk.CTkLabel(
            parent,
            text="Con FightCade en foco, presiona esta tecla o botón para ejecutar\n"
                 "el combo activo en el editor sin necesidad de volver a la app.",
            font=FONT_SMALL, text_color=MUTED, justify="left",
        ).pack(padx=14, pady=(4, 14), anchor="w")

        # Timing
        timing = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=8)
        timing.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(timing, text="Tiempos de ejecución", font=FONT_HEADER,
                     text_color=GOLD).pack(anchor="w", padx=12, pady=(10, 6))

        self._pre_lbl_val = ctk.StringVar(value=f"{self._pre_delay}s")
        self._step_lbl_val = ctk.StringVar(value=f"{int(self._exec_delay*1000)}ms")

        self._make_slider(
            timing,
            label="Espera inicial (para alt-tab):",
            var=self._pre_lbl_val,
            from_=0, to=10, steps=10,
            initial=self._pre_delay,
            fmt=lambda v: f"{round(v):.0f}s",
            on_change=lambda v: setattr(self, "_pre_delay", round(v)),
        )
        self._make_slider(
            timing,
            label="Delay entre pasos:",
            var=self._step_lbl_val,
            from_=0, to=200, steps=40,
            initial=self._exec_delay * 1000,
            fmt=lambda v: f"{round(v / 5) * 5:.0f}ms",
            on_change=lambda v: setattr(self, "_exec_delay", round(v / 5) * 5 / 1000.0),
        )

    def _make_slider(self, parent, label, var, from_, to, steps, initial, fmt, on_change):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(row, text=label, font=FONT_BODY, text_color=TEXT,
                     width=240, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(row, textvariable=var, font=FONT_BODY,
                               text_color=CYAN, width=55)
        val_lbl.pack(side="right", padx=8)
        slider = ctk.CTkSlider(row, from_=from_, to=to, number_of_steps=steps,
                               button_color=PRIMARY, progress_color=PRIMARY)
        slider.set(initial)
        slider.pack(side="right", expand=True, fill="x", padx=8)

        def _cb(v):
            on_change(v)
            var.set(fmt(v))

        slider.configure(command=_cb)

    def _build_gamepads_tab(self, parent):
        ctk.CTkLabel(parent, text="Gamepads detectados:", font=FONT_HEADER,
                     text_color=GOLD).pack(anchor="w", padx=12, pady=(12, 6))

        self._pad_frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=8)
        self._pad_frame.pack(fill="x", padx=10, pady=4)
        self._refresh_pad_list()

        ctk.CTkButton(parent, text="↺  Buscar gamepads de nuevo", font=FONT_BODY,
                      fg_color=SURFACE, hover_color=BORDER, corner_radius=6,
                      command=self._refresh_pad_list).pack(padx=10, pady=8, anchor="w")

        if not self.input_mgr.pygame_available:
            ctk.CTkLabel(parent,
                         text="pygame no está instalado — soporte de gamepad desactivado.\n"
                              "Instala con:  pip install pygame",
                         font=FONT_SMALL, text_color=AMBER, justify="left"
                         ).pack(padx=12, pady=8, anchor="w")
        else:
            ctk.CTkLabel(
                parent,
                text="Tip: usa 'Capturar' en las pestañas Movimiento y Ataques\n"
                     "para asignar botones del gamepad a cada acción.",
                font=FONT_SMALL, text_color=MUTED, justify="left",
            ).pack(padx=12, pady=8, anchor="w")

    def _refresh_pad_list(self):
        for w in self._pad_frame.winfo_children():
            w.destroy()
        self.input_mgr.refresh_joysticks()
        joysticks = self.input_mgr.get_joystick_names()
        if not joysticks:
            ctk.CTkLabel(self._pad_frame, text="No se detectaron gamepads conectados.",
                         font=FONT_BODY, text_color=MUTED, pady=14).pack()
        else:
            for idx, name in joysticks:
                r = ctk.CTkFrame(self._pad_frame, fg_color="transparent")
                r.pack(fill="x", padx=12, pady=6)
                ctk.CTkLabel(r, text=f"[{idx}]", font=FONT_BODY,
                             text_color=PRIMARY, width=28).pack(side="left")
                ctk.CTkLabel(r, text=name, font=FONT_BODY,
                             text_color=TEXT).pack(side="left", padx=8)

    # ── BINDING ROWS ──────────────────────────────────────────────────────────

    def _make_row(self, parent, section, action_id, label_text, binding):
        row = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=6)
        row.pack(fill="x", padx=4, pady=3)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=label_text, font=FONT_BODY, text_color=TEXT,
                     width=150, anchor="w").grid(row=0, column=0, padx=(12, 6), pady=8)

        display = format_binding(binding) if binding else "— sin asignar —"
        lbl = ctk.CTkLabel(row, text=display, font=FONT_BODY,
                           text_color=CYAN if binding else MUTED, anchor="w")
        lbl.grid(row=0, column=1, sticky="w", padx=6)

        ctk.CTkButton(
            row, text="Capturar", width=80, font=FONT_SMALL,
            fg_color=PRIMARY, hover_color=PHOVER, corner_radius=4,
            command=lambda s=section, a=action_id, l=lbl: self._start_capture(s, a, l)
        ).grid(row=0, column=2, padx=4, pady=6)

        ctk.CTkButton(
            row, text="Limpiar", width=70, font=FONT_SMALL,
            fg_color=SURFACE, hover_color=BORDER, corner_radius=4,
            command=lambda s=section, a=action_id, l=lbl: self._clear_binding(s, a, l)
        ).grid(row=0, column=3, padx=(0, 8), pady=6)

    # ── CAPTURE LOGIC ─────────────────────────────────────────────────────────

    def _start_capture(self, section, action_id, label):
        if self._capturing:
            return
        self._capturing = (section, action_id, label)
        label.configure(text="[ Presiona tecla o botón... ]", text_color=AMBER)
        self.status_lbl.configure(text="Esperando input... (Esc para cancelar)",
                                   text_color=AMBER)
        self.bind("<KeyPress>", self._on_key_capture)
        self.bind("<Escape>",   self._cancel_capture)
        self._poll_gamepad_capture()

    def _on_key_capture(self, event):
        if not self._capturing:
            return
        if event.keysym in IGNORE_KEYSYMS:
            return
        self.unbind("<KeyPress>")
        self.unbind("<Escape>")
        section, action_id, label = self._capturing
        self._capturing = None
        self._apply_binding(section, action_id, label,
                            {"type": "keyboard", "key": event.keysym})

    def _poll_gamepad_capture(self):
        if not self._capturing:
            return
        result = self.input_mgr.poll_for_capture()
        if result:
            self.unbind("<KeyPress>")
            self.unbind("<Escape>")
            section, action_id, label = self._capturing
            self._capturing = None
            self._apply_binding(section, action_id, label, result)
        else:
            self.after(50, self._poll_gamepad_capture)

    def _cancel_capture(self, event=None):
        if not self._capturing:
            return
        self.unbind("<KeyPress>")
        self.unbind("<Escape>")
        section, action_id, label = self._capturing
        self._capturing = None
        # Restore previous display
        if section == "dirs":
            b = self._dirs.get(action_id)
        elif section == "attacks":
            b = self._attacks.get(action_id)
        else:
            b = self._macro_trigger
        label.configure(text=format_binding(b) if b else "— sin asignar —",
                        text_color=CYAN if b else MUTED)
        self.status_lbl.configure(text="Captura cancelada.", text_color=MUTED)

    def _apply_binding(self, section, action_id, label, binding):
        if section == "dirs":
            self._dirs[action_id] = binding
        elif section == "attacks":
            self._attacks[action_id] = binding
        elif section == "trigger":
            self._macro_trigger = binding
        label.configure(text=format_binding(binding), text_color=GREEN)
        self.status_lbl.configure(text=f"✓ Asignado: {format_binding(binding)}",
                                   text_color=GREEN)

    def _clear_binding(self, section, action_id, label):
        if section == "dirs":
            self._dirs.pop(action_id, None)
        elif section == "attacks":
            self._attacks.pop(action_id, None)
        label.configure(text="— sin asignar —", text_color=MUTED)

    def _clear_trigger(self):
        self._macro_trigger = {}
        self._trig_lbl.configure(text="— sin asignar —", text_color=MUTED)

    # ── SAVE / CANCEL ─────────────────────────────────────────────────────────

    def _save(self):
        if self._capturing:
            self._cancel_capture()
        game_id = self.game.id if self.game else "default"
        self.settings.setdefault("key_mappings", {})[game_id] = {
            "dirs":    self._dirs,
            "attacks": self._attacks,
        }
        self.settings["macro_trigger"] = self._macro_trigger
        self.settings["exec_delay"]    = self._exec_delay
        self.settings["pre_delay"]     = self._pre_delay
        if self.on_save:
            self.on_save(self.settings)
        self.destroy()

    def _cancel(self):
        if self._capturing:
            self._cancel_capture()
        self.destroy()
