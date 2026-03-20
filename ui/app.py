# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import sys
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import StorageManager
from core.executor import MacroExecutor
from core.game import Game, LAYOUT_BUTTONS, LAYOUT_DEFAULT_KEYS, BUTTON_COLORS, DIRECTION_KEYS
from core.combo import Combo, ComboStep
from core.input_manager import InputManager, format_binding
from core.virtual_gamepad import VirtualGamepad, DEFAULT_ATTACK_MAP

# ─── THEME ────────────────────────────────────────────────────────────────────
BG       = "#0A0A0F"
SURFACE  = "#12121A"
CARD     = "#1C1C2E"
BORDER   = "#2A2A40"
PRIMARY  = "#FF4500"
PHOVER   = "#CC3300"
CYAN     = "#00D4FF"
GOLD     = "#FFD700"
GREEN    = "#00C853"
AMBER    = "#FF9800"
RED      = "#FF1744"
TEXT     = "#F0F0FF"
MUTED    = "#8888AA"

FONT_TITLE  = ("Consolas", 20, "bold")
FONT_HEADER = ("Consolas", 13, "bold")
FONT_BODY   = ("Consolas", 11)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Courier New", 11)

DIR_SYMBOLS = {
    "7": "↖", "8": "↑", "9": "↗",
    "4": "←", "5": "·", "6": "→",
    "1": "↙", "2": "↓", "3": "↘",
}

DPAD_LAYOUT = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
]


def _dim_color(hex_color: str) -> str:
    """Return a darkened version of a hex color (for deselected button state)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * 0.30), int(g * 0.30), int(b * 0.30)
    return f"#{r:02X}{g:02X}{b:02X}"


class SupeRoisApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("SupeRois — Fighting Game Combo Manager")
        self.root.geometry("1280x800")
        self.root.minsize(1050, 680)
        self.root.configure(fg_color=BG)

        self.storage = StorageManager()
        self.executor = MacroExecutor()
        self.input_mgr = InputManager()
        self.vpad = VirtualGamepad()  # virtual Xbox 360 controller (requires ViGEm)

        # State
        self.games = self.storage.load_games()
        self.settings = self.storage.load_settings()
        self.current_game = None
        self.current_character = None
        self.combos = []
        self.selected_combo = None

        # Editor state
        self.editing_combo = None
        self.current_steps = []
        self.pending_direction = "5"
        self.pending_attacks = []
        self.combine_next = False
        self.pending_hotkey = None           # hotkey being set for current combo
        self._editor_capturing_hotkey = False

        # Mirror mode
        self.mirror_mode = False

        # Master macro switch (hotkeys only fire when ON)
        self.macros_enabled = False

        # HWND of the game window captured when a hotkey fires
        self._game_hwnd = None

        self._build_ui()
        self._select_game_by_id(self.settings.get("last_game", self.games[0].id if self.games else None))

    def run(self):
        self.root.mainloop()

    # ── BUILD UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=0, minsize=230)
        self.root.grid_columnconfigure(1, weight=0, minsize=270)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_sidebar()
        self._build_combo_list_panel()
        self._build_editor_panel()

    def _build_topbar(self):
        bar = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0, border_width=1, border_color=BORDER)
        bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(bar, text="⚡ SUPEROIS", font=FONT_TITLE,
                              text_color=CYAN, padx=20, pady=12)
        title.grid(row=0, column=0, sticky="w")

        sub = ctk.CTkLabel(bar, text="Fighting Game Combo Manager for FightCade2",
                            font=FONT_SMALL, text_color=MUTED)
        sub.grid(row=0, column=1, sticky="w", padx=5)

        # Right side: warnings + settings button
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=10)

        if not self.executor.available:
            ctk.CTkLabel(right, text="⚠ sin librería de input",
                         font=FONT_SMALL, text_color=AMBER).pack(side="left", padx=10)
        else:
            backend_color = GREEN if self.executor.backend == "pydirectinput" else AMBER
            ctk.CTkLabel(right, text=f"input: {self.executor.backend}",
                         font=FONT_SMALL, text_color=backend_color).pack(side="left", padx=10)

        if self.vpad.available:
            ctk.CTkLabel(right, text="🎮 vgamepad: OK",
                         font=FONT_SMALL, text_color=GREEN).pack(side="left", padx=10)
        else:
            vpad_lbl = ctk.CTkLabel(
                right,
                text="🎮 vgamepad: ⚠ clic para ayuda",
                font=FONT_SMALL, text_color=AMBER, cursor="hand2"
            )
            vpad_lbl.pack(side="left", padx=10)
            vpad_lbl.bind("<Button-1>", lambda *_: self._show_vgamepad_help())

        self.macros_btn = ctk.CTkButton(
            right, text="⚡ Macros: OFF", font=FONT_BODY,
            fg_color=CARD, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=MUTED, corner_radius=6, width=135,
            command=self._toggle_macros
        )
        self.macros_btn.pack(side="right", padx=6, pady=8)

        self.mirror_btn = ctk.CTkButton(
            right, text="🪞 Espejo: OFF", font=FONT_BODY,
            fg_color=CARD, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=MUTED, corner_radius=6, width=130,
            command=self._toggle_mirror
        )
        self.mirror_btn.pack(side="right", padx=6, pady=8)

        ctk.CTkButton(
            right, text="⚙  Config", font=FONT_BODY,
            fg_color=CARD, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT, corner_radius=6, width=100,
            command=self._open_settings
        ).pack(side="right", padx=6, pady=8)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0,
                                    border_width=1, border_color=BORDER)
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkLabel(self.sidebar, text="JUEGOS", font=FONT_HEADER,
                            text_color=GOLD, pady=10)
        hdr.grid(row=0, column=0, sticky="ew", padx=10)

        # Scrollable game list
        self.game_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent",
                                                   scrollbar_button_color=BORDER)
        self.game_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.game_scroll.grid_columnconfigure(0, weight=1)

        self.game_buttons = {}
        self._populate_game_list()

    def _populate_game_list(self):
        for w in self.game_scroll.winfo_children():
            w.destroy()
        self.game_buttons = {}

        # Group by series
        series_groups = {}
        for g in self.games:
            s = g.series or "Other"
            series_groups.setdefault(s, []).append(g)

        row = 0
        for series, games in series_groups.items():
            lbl = ctk.CTkLabel(self.game_scroll, text=series.upper(), font=FONT_SMALL,
                               text_color=MUTED, anchor="w")
            lbl.grid(row=row, column=0, sticky="ew", padx=8, pady=(10, 2))
            row += 1
            for g in games:
                btn = ctk.CTkButton(
                    self.game_scroll, text=g.short_name, anchor="w",
                    font=FONT_BODY, fg_color="transparent", text_color=TEXT,
                    hover_color=BORDER, corner_radius=4,
                    command=lambda gid=g.id: self._select_game_by_id(gid)
                )
                btn.grid(row=row, column=0, sticky="ew", padx=4, pady=1)
                self.game_buttons[g.id] = btn
                row += 1

    def _select_game_by_id(self, game_id):
        if not game_id:
            return
        # Deselect previous
        if self.current_game:
            btn = self.game_buttons.get(self.current_game.id)
            if btn:
                btn.configure(fg_color="transparent", text_color=TEXT)

        self.current_game = self.storage.get_game(game_id)
        if not self.current_game:
            return

        # Highlight selected
        btn = self.game_buttons.get(game_id)
        if btn:
            btn.configure(fg_color=PRIMARY, text_color="white")

        # Select first character
        chars = self.current_game.characters
        self.current_character = chars[0] if chars else None

        self._refresh_combo_list()
        self._refresh_char_selector()
        self._refresh_attack_buttons()
        self._clear_editor()

        self.settings["last_game"] = game_id
        self.storage.save_settings(self.settings)

    # ── COMBO LIST PANEL ──────────────────────────────────────────────────────

    def _build_combo_list_panel(self):
        panel = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0,
                             border_width=1, border_color=BORDER)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header + char selector
        self.list_header = ctk.CTkLabel(panel, text="COMBOS", font=FONT_HEADER,
                                         text_color=GOLD, pady=8)
        self.list_header.grid(row=0, column=0, sticky="ew", padx=10)

        # Char dropdown frame
        char_frame = ctk.CTkFrame(panel, fg_color=CARD, corner_radius=6)
        char_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(35, 0))
        char_frame.grid_columnconfigure(0, weight=1)

        char_lbl = ctk.CTkLabel(char_frame, text="Personaje:", font=FONT_SMALL,
                                 text_color=MUTED, anchor="w")
        char_lbl.grid(row=0, column=0, sticky="w", padx=8, pady=(6, 0))

        self.char_var = ctk.StringVar()
        self.char_combo = ctk.CTkComboBox(
            char_frame, variable=self.char_var, font=FONT_BODY,
            fg_color=CARD, border_color=BORDER, button_color=PRIMARY,
            dropdown_fg_color=SURFACE, command=self._on_char_changed,
            state="readonly"
        )
        self.char_combo.grid(row=1, column=0, sticky="ew", padx=8, pady=(2, 8))

        # Scrollable combo list
        self.combo_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent",
                                                    scrollbar_button_color=BORDER)
        self.combo_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.combo_scroll.grid_columnconfigure(0, weight=1)

        # Bottom toolbar
        toolbar = ctk.CTkFrame(panel, fg_color=CARD, corner_radius=0)
        toolbar.grid(row=2, column=0, sticky="ew")

        ctk.CTkButton(
            toolbar, text="+ Nuevo Combo", font=FONT_BODY, fg_color=GREEN,
            hover_color="#009624", text_color="white", corner_radius=4,
            command=self._new_combo
        ).pack(side="left", padx=8, pady=8)

        ctk.CTkButton(
            toolbar, text="Borrar", font=FONT_BODY, fg_color=RED,
            hover_color="#C41230", text_color="white", corner_radius=4,
            command=self._delete_selected_combo
        ).pack(side="right", padx=8, pady=8)

    def _refresh_char_selector(self):
        if not self.current_game:
            self.char_combo.configure(values=[])
            return
        names = [c.name for c in self.current_game.characters]
        self.char_combo.configure(values=names)
        if self.current_character:
            self.char_var.set(self.current_character.name)
        elif names:
            self.char_var.set(names[0])
            self.current_character = self.current_game.characters[0]

    def _on_char_changed(self, value):
        if not self.current_game:
            return
        for c in self.current_game.characters:
            if c.name == value:
                self.current_character = c
                break
        self._refresh_combo_list()

    def _refresh_combo_list(self):
        for w in self.combo_scroll.winfo_children():
            w.destroy()

        if not self.current_game:
            return

        self.combos = self.storage.load_combos(self.current_game.id)
        self._register_all_combo_hotkeys()
        char_id = self.current_character.id if self.current_character else None
        filtered = [c for c in self.combos if char_id is None or c.character_id == char_id]

        game_name = self.current_game.short_name
        char_name = self.current_character.name if self.current_character else "All"
        self.list_header.configure(text=f"COMBOS — {game_name} — {char_name}")

        if not filtered:
            ctk.CTkLabel(self.combo_scroll, text="No hay combos aún.\nHaz clic en '+ Nuevo Combo'",
                         font=FONT_BODY, text_color=MUTED).pack(pady=40)
            return

        for combo in filtered:
            self._make_combo_card(combo)

    def _make_combo_card(self, combo: Combo):
        card = ctk.CTkFrame(self.combo_scroll, fg_color=CARD, corner_radius=8,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=4, pady=3)
        card.grid_columnconfigure(0, weight=1)

        name_lbl = ctk.CTkLabel(card, text=combo.name, font=FONT_HEADER,
                                  text_color=TEXT, anchor="w")
        name_lbl.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))

        notation = combo.notation or "(sin pasos)"
        notif_lbl = ctk.CTkLabel(card, text=notation, font=FONT_MONO,
                                   text_color=CYAN, anchor="w")
        notif_lbl.grid(row=1, column=0, sticky="ew", padx=10)

        meta_parts = []
        if combo.tags:
            meta_parts.append("  ".join(f"[{t}]" for t in combo.tags))
        if combo.hotkey:
            meta_parts.append(f"🔑 {format_binding(combo.hotkey)}")
        if meta_parts:
            ctk.CTkLabel(card, text="   ".join(meta_parts), font=FONT_SMALL,
                          text_color=GOLD, anchor="w").grid(row=2, column=0, sticky="w", padx=10)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, rowspan=3, padx=6, pady=4)

        ctk.CTkButton(
            btn_frame, text="Editar", width=60, font=FONT_SMALL,
            fg_color=PRIMARY, hover_color=PHOVER, corner_radius=4,
            command=lambda c=combo: self._edit_combo(c)
        ).pack(pady=2)

        ctk.CTkButton(
            btn_frame, text="Ejecutar", width=60, font=FONT_SMALL,
            fg_color=AMBER, hover_color="#CC7A00", text_color="black", corner_radius=4,
            command=lambda c=combo: self._run_combo(c)
        ).pack(pady=2)

        # Click card to select
        card.bind("<Button-1>", lambda e, c=combo: self._select_combo(c))
        name_lbl.bind("<Button-1>", lambda e, c=combo: self._select_combo(c))

    def _select_combo(self, combo):
        self.selected_combo = combo

    # ── EDITOR PANEL ──────────────────────────────────────────────────────────

    def _build_editor_panel(self):
        self.editor_panel = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0,
                                          border_width=1, border_color=BORDER)
        self.editor_panel.grid(row=1, column=2, sticky="nsew")
        self.editor_panel.grid_columnconfigure(0, weight=1)
        self.editor_panel.grid_rowconfigure(3, weight=1)  # sequence gets the space

        self._build_editor_form()
        self._build_sequence_area()
        self._build_input_area()
        self._build_editor_toolbar()

    def _build_editor_form(self):
        form = ctk.CTkFrame(self.editor_panel, fg_color=CARD, corner_radius=8)
        form.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="EDITOR DE COMBOS", font=FONT_HEADER,
                     text_color=GOLD).grid(row=0, column=0, columnspan=3, pady=(8, 4), padx=12, sticky="w")

        ctk.CTkLabel(form, text="Nombre:", font=FONT_BODY, text_color=MUTED).grid(
            row=1, column=0, sticky="w", padx=(12, 4), pady=4)
        self.name_entry = ctk.CTkEntry(form, font=FONT_BODY, placeholder_text="Ej: Hadouken",
                                        fg_color=SURFACE, border_color=BORDER)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        ctk.CTkLabel(form, text="Descripción:", font=FONT_BODY, text_color=MUTED).grid(
            row=2, column=0, sticky="w", padx=(12, 4), pady=4)
        self.desc_entry = ctk.CTkEntry(form, font=FONT_BODY, placeholder_text="Opcional...",
                                        fg_color=SURFACE, border_color=BORDER)
        self.desc_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=4)

        ctk.CTkLabel(form, text="Tags:", font=FONT_BODY, text_color=MUTED).grid(
            row=3, column=0, sticky="w", padx=(12, 4), pady=4)
        self.tags_entry = ctk.CTkEntry(form, font=FONT_BODY,
                                        placeholder_text="fireball, especial, bnb",
                                        fg_color=SURFACE, border_color=BORDER)
        self.tags_entry.grid(row=3, column=1, sticky="ew", padx=4, pady=4)

        # Hotkey row
        hk_row = ctk.CTkFrame(form, fg_color="transparent")
        hk_row.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 10))
        ctk.CTkLabel(hk_row, text="Hotkey:", font=FONT_BODY, text_color=MUTED,
                     width=90, anchor="w").pack(side="left", padx=(4, 6))
        self.hotkey_lbl = ctk.CTkLabel(hk_row, text="— sin asignar —",
                                        font=FONT_BODY, text_color=MUTED)
        self.hotkey_lbl.pack(side="left")
        ctk.CTkButton(hk_row, text="Capturar", width=80, font=FONT_SMALL,
                      fg_color=PRIMARY, hover_color=PHOVER, corner_radius=4,
                      command=self._capture_combo_hotkey).pack(side="left", padx=(10, 4))
        ctk.CTkButton(hk_row, text="Limpiar", width=70, font=FONT_SMALL,
                      fg_color=SURFACE, hover_color=BORDER, corner_radius=4,
                      command=self._clear_combo_hotkey).pack(side="left")

    def _build_sequence_area(self):
        seq_frame = ctk.CTkFrame(self.editor_panel, fg_color=CARD, corner_radius=8)
        seq_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        seq_frame.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(seq_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        ctk.CTkLabel(hdr, text="SECUENCIA:", font=FONT_HEADER, text_color=GOLD).pack(side="left")
        ctk.CTkButton(
            hdr, text="Limpiar Todo", font=FONT_SMALL, width=90,
            fg_color=RED, hover_color="#C41230", corner_radius=4,
            command=self._clear_steps
        ).pack(side="right")
        ctk.CTkButton(
            hdr, text="← Deshacer", font=FONT_SMALL, width=90,
            fg_color=SURFACE, hover_color=BORDER, corner_radius=4,
            command=self._remove_last_step
        ).pack(side="right", padx=4)

        # Sequence scroll (horizontal feel via wraplength)
        self.seq_frame = ctk.CTkScrollableFrame(
            seq_frame, fg_color="transparent", height=60,
            scrollbar_button_color=BORDER, orientation="horizontal"
        )
        self.seq_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        self._refresh_sequence_display()

    def _build_input_area(self):
        input_area = ctk.CTkFrame(self.editor_panel, fg_color=CARD, corner_radius=8)
        input_area.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        input_area.grid_columnconfigure(0, weight=1)
        input_area.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_area, text="INPUTS:", font=FONT_HEADER, text_color=GOLD).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 4))

        # Left: D-Pad
        dpad_frame = ctk.CTkFrame(input_area, fg_color=SURFACE, corner_radius=8)
        dpad_frame.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")
        ctk.CTkLabel(dpad_frame, text="DIRECCIÓN", font=FONT_SMALL, text_color=MUTED).pack(pady=(6, 2))
        self._build_dpad(dpad_frame)

        # Right: Attack buttons + add step controls
        atk_frame = ctk.CTkFrame(input_area, fg_color=SURFACE, corner_radius=8)
        atk_frame.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")
        ctk.CTkLabel(atk_frame, text="ATAQUES", font=FONT_SMALL, text_color=MUTED).pack(pady=(6, 2))
        self.atk_container = ctk.CTkFrame(atk_frame, fg_color="transparent")
        self.atk_container.pack()
        self.atk_buttons = {}
        self._build_attack_buttons()

        # Hold + Add Step row
        ctrl_row = ctk.CTkFrame(input_area, fg_color="transparent")
        ctrl_row.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10))

        self.hold_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrl_row, text="Mantener (hold)", variable=self.hold_var,
                        font=FONT_BODY, text_color=TEXT, fg_color=PRIMARY,
                        hover_color=PHOVER).pack(side="left", padx=10)

        ctk.CTkButton(
            ctrl_row, text="➕ Agregar Paso", font=FONT_BODY, fg_color=PRIMARY,
            hover_color=PHOVER, corner_radius=6, width=150,
            command=self._add_step
        ).pack(side="left", padx=10)

    def _build_dpad(self, parent):
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(pady=6)
        self.dir_buttons = {}

        for r, row in enumerate(DPAD_LAYOUT):
            for c, key in enumerate(row):
                sym = DIR_SYMBOLS[key]
                is_neutral = key == "5"
                btn = ctk.CTkButton(
                    grid, text=sym, width=48, height=48,
                    font=("Consolas", 16, "bold"),
                    fg_color=SURFACE if not is_neutral else BORDER,
                    hover_color=BORDER if not is_neutral else BORDER,
                    border_color=BORDER, border_width=1,
                    text_color=MUTED if is_neutral else TEXT,
                    corner_radius=6,
                    command=(None if is_neutral else lambda k=key: self._select_direction(k))
                )
                btn.grid(row=r, column=c, padx=2, pady=2)
                if not is_neutral:
                    self.dir_buttons[key] = btn

        # Neutral reset button below dpad
        ctk.CTkButton(
            parent, text="Neutro (5)", font=FONT_SMALL, width=120, height=28,
            fg_color=SURFACE, hover_color=BORDER, corner_radius=4, text_color=MUTED,
            command=lambda: self._select_direction("5")
        ).pack(pady=(0, 6))

    def _build_attack_buttons(self):
        for w in self.atk_container.winfo_children():
            w.destroy()
        self.atk_buttons = {}

        if not self.current_game:
            return

        buttons = self.current_game.buttons
        colors = BUTTON_COLORS

        if len(buttons) == 6:
            # 2 rows of 3
            rows = [buttons[:3], buttons[3:]]
        elif len(buttons) == 4:
            rows = [buttons[:2], buttons[2:]]
        elif len(buttons) == 5:
            rows = [buttons[:3], buttons[3:]]
        else:
            rows = [buttons]

        for ri, row_btns in enumerate(rows):
            frame = ctk.CTkFrame(self.atk_container, fg_color="transparent")
            frame.pack(pady=2)
            for bi, btn_name in enumerate(row_btns):
                color = colors.get(btn_name, "#888888")
                dim = _dim_color(color)
                btn = ctk.CTkButton(
                    frame, text=btn_name, width=62, height=42,
                    font=FONT_BODY,
                    fg_color=dim,
                    hover_color=color,
                    border_color=color, border_width=2,
                    text_color=TEXT, corner_radius=8,
                    command=lambda b=btn_name: self._toggle_attack(b)
                )
                btn.pack(side="left", padx=3)
                self.atk_buttons[btn_name] = (btn, color)

    def _refresh_attack_buttons(self):
        self._build_attack_buttons()

    def _build_editor_toolbar(self):
        toolbar = ctk.CTkFrame(self.editor_panel, fg_color=CARD, corner_radius=0)
        toolbar.grid(row=4, column=0, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(toolbar, fg_color="transparent")
        left.pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            left, text="💾 Guardar Combo", font=FONT_BODY, fg_color=GREEN,
            hover_color="#009624", corner_radius=6, width=160,
            command=self._save_combo
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            left, text="Cancelar", font=FONT_BODY, fg_color=SURFACE,
            hover_color=BORDER, corner_radius=6, width=90,
            command=self._clear_editor
        ).pack(side="left", padx=4)

        right = ctk.CTkFrame(toolbar, fg_color="transparent")
        right.pack(side="right", padx=10, pady=10)

        self.exec_btn = ctk.CTkButton(
            right, text="▶ EJECUTAR MACRO", font=FONT_HEADER, fg_color=AMBER,
            hover_color="#CC7A00", text_color="black", corner_radius=6, width=200,
            command=self._run_current_steps
        )
        self.exec_btn.pack(side="right", padx=4)

        self.stop_btn = ctk.CTkButton(
            right, text="■ Detener", font=FONT_BODY, fg_color=RED,
            hover_color="#C41230", corner_radius=6, width=90,
            command=self._stop_macro, state="disabled"
        )
        self.stop_btn.pack(side="right", padx=4)

        self.status_lbl = ctk.CTkLabel(toolbar, text="Listo.", font=FONT_SMALL,
                                        text_color=MUTED)
        self.status_lbl.pack(side="left", padx=20)

    # ── EDITOR ACTIONS ────────────────────────────────────────────────────────

    def _select_direction(self, key):
        self.pending_direction = key
        # Update UI
        for k, btn in self.dir_buttons.items():
            if k == key:
                btn.configure(fg_color=CYAN, text_color="black")
            else:
                btn.configure(fg_color=SURFACE, text_color=TEXT)

    def _toggle_attack(self, btn_name):
        if btn_name in self.pending_attacks:
            self.pending_attacks.remove(btn_name)
        else:
            self.pending_attacks.append(btn_name)

        btn, color = self.atk_buttons[btn_name]
        if btn_name in self.pending_attacks:
            btn.configure(fg_color=color, text_color="black")
        else:
            btn.configure(fg_color=_dim_color(color), text_color=TEXT)

    def _add_step(self):
        step = ComboStep(
            direction=self.pending_direction,
            attacks=list(self.pending_attacks),
            hold=self.hold_var.get(),
            delay_ms=0
        )
        self.current_steps.append(step)
        self._reset_input_selection()
        self._refresh_sequence_display()

    def _reset_input_selection(self):
        self.pending_direction = "5"
        self.pending_attacks = []
        self.hold_var.set(False)

        for k, btn in self.dir_buttons.items():
            btn.configure(fg_color=SURFACE, text_color=TEXT)

        for btn_name, (btn, color) in self.atk_buttons.items():
            btn.configure(fg_color=_dim_color(color), text_color=TEXT)

    def _remove_last_step(self):
        if self.current_steps:
            self.current_steps.pop()
            self._refresh_sequence_display()

    def _clear_steps(self):
        self.current_steps = []
        self._refresh_sequence_display()

    def _refresh_sequence_display(self):
        for w in self.seq_frame.winfo_children():
            w.destroy()

        if not self.current_steps:
            ctk.CTkLabel(self.seq_frame, text="[ Secuencia vacía — agrega pasos abajo ]",
                         font=FONT_SMALL, text_color=MUTED).pack(padx=10, pady=10)
            return

        for i, step in enumerate(self.current_steps):
            chip_text = DIR_SYMBOLS.get(step.direction, step.direction)
            if step.attacks:
                chip_text += "+" + "+".join(step.attacks)
            if step.hold:
                chip_text = f"[{chip_text}]"

            chip = ctk.CTkLabel(
                self.seq_frame, text=chip_text,
                font=FONT_BODY, text_color="black",
                fg_color=CYAN, corner_radius=6,
                padx=10, pady=6
            )
            chip.pack(side="left", padx=3, pady=8)

            if i < len(self.current_steps) - 1:
                arr = ctk.CTkLabel(self.seq_frame, text="→", font=FONT_BODY, text_color=MUTED)
                arr.pack(side="left")

    # ── COMBO CRUD ────────────────────────────────────────────────────────────

    def _new_combo(self):
        self._clear_editor()
        self.editing_combo = None
        self.name_entry.focus()
        self.status_lbl.configure(text="Modo: Crear nuevo combo", text_color=GREEN)

    def _edit_combo(self, combo: Combo):
        self.editing_combo = combo
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, combo.name)
        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, combo.description)
        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(combo.tags))
        self.current_steps = list(combo.steps)
        self.pending_hotkey = combo.hotkey
        self._update_hotkey_label()
        self._refresh_sequence_display()
        self.status_lbl.configure(text=f"Editando: {combo.name}", text_color=AMBER)

    def _clear_editor(self):
        self.editing_combo = None
        self.current_steps = []
        self.pending_hotkey = None
        self.name_entry.delete(0, "end")
        self.desc_entry.delete(0, "end")
        self.tags_entry.delete(0, "end")
        self._update_hotkey_label()
        self._reset_input_selection()
        self._refresh_sequence_display()
        self.status_lbl.configure(text="Listo.", text_color=MUTED)

    def _save_combo(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("SupeRois", "El combo necesita un nombre.", parent=self.root)
            return
        if not self.current_game:
            messagebox.showwarning("SupeRois", "Selecciona un juego primero.", parent=self.root)
            return
        if not self.current_steps:
            messagebox.showwarning("SupeRois", "Agrega al menos un paso al combo.", parent=self.root)
            return

        tags_raw = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        char_id = self.current_character.id if self.current_character else "all"

        combos = self.storage.load_combos(self.current_game.id)

        if self.editing_combo:
            for i, c in enumerate(combos):
                if c.id == self.editing_combo.id:
                    combos[i].name = name
                    combos[i].description = self.desc_entry.get().strip()
                    combos[i].tags = tags
                    combos[i].steps = list(self.current_steps)
                    combos[i].hotkey = self.pending_hotkey
                    from datetime import datetime
                    combos[i].modified_at = datetime.now().isoformat()
                    break
        else:
            new_combo = Combo(
                name=name,
                character_id=char_id,
                game_id=self.current_game.id,
                steps=list(self.current_steps),
                description=self.desc_entry.get().strip(),
                tags=tags,
                hotkey=self.pending_hotkey,
            )
            combos.append(new_combo)

        self.storage.save_combos(self.current_game.id, combos)
        self._clear_editor()
        self._refresh_combo_list()
        self.status_lbl.configure(text=f"'{name}' guardado correctamente.", text_color=GREEN)

    def _delete_selected_combo(self):
        if not self.selected_combo:
            messagebox.showinfo("SupeRois", "Selecciona un combo de la lista primero.", parent=self.root)
            return
        if messagebox.askyesno("Borrar Combo",
                               f"¿Borrar '{self.selected_combo.name}'? Esta acción no se puede deshacer.",
                               parent=self.root):
            combos = self.storage.load_combos(self.current_game.id)
            combos = [c for c in combos if c.id != self.selected_combo.id]
            self.storage.save_combos(self.current_game.id, combos)
            self.selected_combo = None
            self._refresh_combo_list()
            self.status_lbl.configure(text="Combo borrado.", text_color=RED)

    # ── MACRO EXECUTION ───────────────────────────────────────────────────────

    def _run_combo(self, combo: Combo):
        self._load_combo_into_editor(combo)
        self._run_current_steps()

    def _load_combo_into_editor(self, combo: Combo):
        self.current_steps = list(combo.steps)
        self._refresh_sequence_display()

    def _run_current_steps(self):
        if not self.current_steps:
            messagebox.showinfo("SupeRois", "No hay pasos en la secuencia.", parent=self.root)
            return

        if not self.executor.available:
            messagebox.showerror("SupeRois",
                                 "pyautogui no está instalado.\n\nInstala con:\npip install pyautogui",
                                 parent=self.root)
            return

        dir_bindings, attack_bindings = self._get_active_bindings()
        dummy_combo = Combo(
            name="temp", character_id="", game_id="",
            steps=list(self.current_steps)
        )

        self.exec_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        def on_countdown(n):
            self.root.after(0, lambda: self.status_lbl.configure(
                text=f"Ejecutando en {n}... (¡cambia a FightCade!)",
                text_color=AMBER
            ))

        def on_start():
            self.root.after(0, lambda: self.status_lbl.configure(
                text="▶ Ejecutando macro...", text_color=PRIMARY))

        def on_complete():
            self.root.after(0, lambda: [
                self.status_lbl.configure(text="✓ Macro completado.", text_color=GREEN),
                self.exec_btn.configure(state="normal"),
                self.stop_btn.configure(state="disabled"),
            ])

        def on_error(msg):
            self.root.after(0, lambda: [
                messagebox.showerror("SupeRois", f"Error: {msg}", parent=self.root),
                self.exec_btn.configure(state="normal"),
                self.stop_btn.configure(state="disabled"),
                self.status_lbl.configure(text="Error en la ejecución.", text_color=RED),
            ])

        # Use virtual gamepad if available, otherwise fall back to keyboard
        active_vpad = self.vpad if self.vpad.available else None
        vpad_map = self.settings.get("vpad_attack_map", DEFAULT_ATTACK_MAP)

        self.executor.execute(
            combo=dummy_combo,
            dir_bindings=dir_bindings,
            attack_bindings=attack_bindings,
            pre_delay=self.settings.get("pre_delay", 3),
            step_delay=self.settings.get("exec_delay", 0.05),
            mirror=self.mirror_mode,
            game_hwnd=self._game_hwnd,
            vpad=active_vpad,
            vpad_attack_map=vpad_map,
            on_countdown=on_countdown,
            on_start=on_start,
            on_complete=on_complete,
            on_error=on_error,
        )

    def _stop_macro(self):
        self.executor.stop()
        self.exec_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_lbl.configure(text="■ Macro detenido.", text_color=RED)

    # ── MACRO SWITCH ──────────────────────────────────────────────────────────

    def _toggle_macros(self):
        self.macros_enabled = not self.macros_enabled
        if self.macros_enabled:
            self.macros_btn.configure(
                text="⚡ Macros: ON",
                fg_color=GREEN, hover_color="#009624",
                text_color="black",
            )
            self.status_lbl.configure(
                text="⚡ Macros ACTIVAS — los hotkeys ejecutarán combos.",
                text_color=GREEN,
            )
        else:
            self.macros_btn.configure(
                text="⚡ Macros: OFF",
                fg_color=CARD, hover_color=BORDER,
                text_color=MUTED,
            )
            self.status_lbl.configure(
                text="Macros desactivadas.", text_color=MUTED,
            )

    # ── MIRROR MODE ───────────────────────────────────────────────────────────

    def _toggle_mirror(self):
        self.mirror_mode = not self.mirror_mode
        if self.mirror_mode:
            self.mirror_btn.configure(text="🪞 Espejo: ON",
                                      fg_color=CYAN, text_color="black")
        else:
            self.mirror_btn.configure(text="🪞 Espejo: OFF",
                                      fg_color=CARD, text_color=MUTED)

    # ── COMBO HOTKEY CAPTURE (in editor) ──────────────────────────────────────

    def _update_hotkey_label(self):
        if self.pending_hotkey:
            self.hotkey_lbl.configure(text=format_binding(self.pending_hotkey),
                                       text_color=GREEN)
        else:
            self.hotkey_lbl.configure(text="— sin asignar —", text_color=MUTED)

    def _capture_combo_hotkey(self):
        if self._editor_capturing_hotkey:
            return
        self._editor_capturing_hotkey = True
        self.hotkey_lbl.configure(text="[ Presiona tecla o botón... ]", text_color=AMBER)
        self.root.bind("<KeyPress>", self._on_editor_hotkey_key)
        self._poll_editor_hotkey_gamepad()

    def _on_editor_hotkey_key(self, event):
        if not self._editor_capturing_hotkey:
            return
        from core.input_manager import IGNORE_KEYSYMS
        if event.keysym in IGNORE_KEYSYMS:
            return
        self.root.unbind("<KeyPress>")
        self._editor_capturing_hotkey = False
        self.pending_hotkey = {"type": "keyboard", "key": event.keysym}
        self._update_hotkey_label()

    def _poll_editor_hotkey_gamepad(self):
        if not self._editor_capturing_hotkey:
            return
        result = self.input_mgr.poll_for_capture()
        if result:
            self.root.unbind("<KeyPress>")
            self._editor_capturing_hotkey = False
            self.pending_hotkey = result
            self._update_hotkey_label()
        else:
            self.root.after(50, self._poll_editor_hotkey_gamepad)

    def _clear_combo_hotkey(self):
        self._editor_capturing_hotkey = False
        self.root.unbind("<KeyPress>")
        self.pending_hotkey = None
        self._update_hotkey_label()

    # ── COMBO HOTKEY REGISTRATION ──────────────────────────────────────────────

    def _register_all_combo_hotkeys(self):
        """Build hotkey_map from all loaded combos and register with InputManager."""
        if not self.current_game:
            return
        combos = self.storage.load_combos(self.current_game.id)
        hotkey_map = {
            c.id: c.hotkey
            for c in combos
            if c.hotkey
        }
        self.input_mgr.register_combo_hotkeys(hotkey_map, self._execute_combo_by_id)

    def _execute_combo_by_id(self, combo_id: str):
        """Execute a specific combo by ID (called from hotkey trigger).
        FightCade is the foreground window at this moment — capture its HWND."""
        if not self.macros_enabled or not self.current_game:
            return
        try:
            self._game_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            self._game_hwnd = None
        combos = self.storage.load_combos(self.current_game.id)
        for combo in combos:
            if combo.id == combo_id:
                self.root.after(0, lambda c=combo: self._load_and_run(c))
                return

    def _load_and_run(self, combo: Combo):
        self.current_steps = list(combo.steps)
        self._refresh_sequence_display()
        self._run_current_steps()

    # ── SETTINGS ──────────────────────────────────────────────────────────────

    def _show_vgamepad_help(self):
        err = self.vpad.error or "Error desconocido."
        messagebox.showinfo(
            "🎮 Gamepad Virtual — Configuración",
            "Para que los macros funcionen dentro de FightCade necesitás:\n\n"
            "1. Instalar ViGEm Bus Driver:\n"
            "   https://github.com/nefarius/ViGEmBus/releases\n"
            "   (descargá el .exe, instalá y REINICIÁ la PC)\n\n"
            "2. pip install vgamepad\n\n"
            "3. En FightCade → Input → configurar Player 1\n"
            "   con el 'Xbox 360 Controller' virtual.\n\n"
            f"Error actual: {err}",
            parent=self.root,
        )

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        SettingsDialog(
            parent=self.root,
            game=self.current_game,
            settings=self.settings,
            input_mgr=self.input_mgr,
            on_save=self._on_settings_saved,
        )

    def _on_settings_saved(self, new_settings: dict):
        self.settings = new_settings
        self.storage.save_settings(new_settings)
        # Re-register macro trigger hotkey/button
        trigger = new_settings.get("macro_trigger", {})
        if trigger:
            self.input_mgr.set_macro_trigger(trigger, self._trigger_macro_from_hotkey)
        self.status_lbl.configure(text="✓ Configuración guardada.", text_color=GREEN)

    def _trigger_macro_from_hotkey(self):
        """Called by InputManager when the global macro hotkey/button is pressed.
        FightCade is the foreground window at this moment — capture its HWND."""
        if not self.macros_enabled or not self.current_steps:
            return
        try:
            self._game_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            self._game_hwnd = None
        self.root.after(0, self._run_current_steps)

    def _get_active_bindings(self):
        """Return (dir_bindings, attack_bindings) for the current game from settings."""
        game_id = self.current_game.id if self.current_game else "default"
        mappings = self.settings.get("key_mappings", {}).get(game_id, {})

        # Direction bindings
        from core.game import DEFAULT_DIR_KEYS
        default_dir = {
            d: {"type": "keyboard", "key": k.capitalize()}
            for d, k in DEFAULT_DIR_KEYS.items()
        }
        dir_bindings = mappings.get("dirs", default_dir)

        # Attack bindings
        default_atk = (
            {btn: {"type": "keyboard", "key": k}
             for btn, k in self.current_game.default_keys.items()}
            if self.current_game else {}
        )
        attack_bindings = mappings.get("attacks", default_atk)

        return dir_bindings, attack_bindings

