import json
import os
from typing import List, Optional
from core.combo import Combo, ComboStep
from core.game import Game, Character, AttackLayout
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(BASE_DIR, "config")
DATA_DIR = os.path.join(BASE_DIR, "data")
GAMES_FILE = os.path.join(CONFIG_DIR, "games.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


class StorageManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self._games_cache: Optional[List[Game]] = None

    def load_games(self) -> List[Game]:
        if self._games_cache is not None:
            return self._games_cache
        with open(GAMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        games = []
        for g in data["games"]:
            layout = AttackLayout(g["attack_layout"])
            chars = [Character(id=c["id"], name=c["name"], portrait=c.get("portrait")) for c in g.get("characters", [])]
            game = Game(
                id=g["id"], name=g["name"], short_name=g["short_name"],
                fightcade_rom=g["fightcade_rom"], attack_layout=layout,
                characters=chars, genre=g.get("genre", "2D Fighter"),
                year=g.get("year", 0), series=g.get("series", "")
            )
            games.append(game)
        self._games_cache = games
        return games

    def get_game(self, game_id: str) -> Optional[Game]:
        for g in self.load_games():
            if g.id == game_id:
                return g
        return None

    def _combos_path(self, game_id: str) -> str:
        game_dir = os.path.join(DATA_DIR, game_id)
        os.makedirs(game_dir, exist_ok=True)
        return os.path.join(game_dir, "combos.json")

    def load_combos(self, game_id: str) -> List[Combo]:
        path = self._combos_path(game_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Combo.from_dict(c) for c in data.get("combos", [])]

    def save_combos(self, game_id: str, combos: List[Combo]):
        path = self._combos_path(game_id)
        tmp = path + ".tmp"
        data = {"game_id": game_id, "version": 1, "combos": [c.to_dict() for c in combos]}
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    def load_settings(self) -> dict:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_game": "ssf2t", "last_character": "", "exec_delay": 0.05, "pre_delay": 3}

    def save_settings(self, settings: dict):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
