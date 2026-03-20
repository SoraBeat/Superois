from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class AttackLayout(Enum):
    SIX_BUTTON_SF = "SIX_BUTTON_SF"      # LP MP HP / LK MK HK
    FOUR_BUTTON_SNK = "FOUR_BUTTON_SNK"  # A B C D
    FOUR_BUTTON_NRS = "FOUR_BUTTON_NRS"  # 1 2 3 4
    FOUR_BUTTON_GG = "FOUR_BUTTON_GG"   # P K S HS (D=dust)
    FIVE_BUTTON_MK = "FIVE_BUTTON_MK"   # HP HK LP LK BL

LAYOUT_BUTTONS = {
    AttackLayout.SIX_BUTTON_SF: ["LP", "MP", "HP", "LK", "MK", "HK"],
    AttackLayout.FOUR_BUTTON_SNK: ["A", "B", "C", "D"],
    AttackLayout.FOUR_BUTTON_NRS: ["1", "2", "3", "4"],
    AttackLayout.FOUR_BUTTON_GG: ["P", "K", "S", "HS", "D"],
    AttackLayout.FIVE_BUTTON_MK: ["HP", "HK", "LP", "LK", "BL"],
}

LAYOUT_DEFAULT_KEYS = {
    AttackLayout.SIX_BUTTON_SF: {"LP": "a", "MP": "s", "HP": "d", "LK": "z", "MK": "x", "HK": "c"},
    AttackLayout.FOUR_BUTTON_SNK: {"A": "a", "B": "s", "C": "d", "D": "z"},
    AttackLayout.FOUR_BUTTON_NRS: {"1": "a", "2": "s", "3": "d", "4": "z"},
    AttackLayout.FOUR_BUTTON_GG: {"P": "a", "K": "s", "S": "d", "HS": "z", "D": "x"},
    AttackLayout.FIVE_BUTTON_MK: {"HP": "a", "HK": "s", "LP": "d", "LK": "z", "BL": "x"},
}

BUTTON_COLORS = {
    # SF6 layout colors
    "LP": "#CCCCCC", "MP": "#44BB44", "HP": "#DD3333",
    "LK": "#3366FF", "MK": "#DDCC00", "HK": "#FF8800",
    # SNK
    "A": "#FF4444", "B": "#4466FF", "C": "#44CC44", "D": "#FFCC00",
    # NRS/MK
    "1": "#CCCCCC", "2": "#44BB44", "3": "#DD3333", "4": "#3366FF",
    # GG
    "P": "#CCCCCC", "K": "#44BB44", "S": "#DD3333", "HS": "#FF8800",
    # MK
    "BL": "#9944BB",
}

DIRECTION_KEYS = {
    "7": ["left", "up"], "8": ["up"], "9": ["up", "right"],
    "4": ["left"], "5": [], "6": ["right"],
    "1": ["down", "left"], "2": ["down"], "3": ["down", "right"],
}

# Maps numpad notation → list of direction names (up/down/left/right)
# Used with user-configurable key mappings
NUMPAD_TO_DIRS = {
    "7": ["up", "left"], "8": ["up"], "9": ["up", "right"],
    "4": ["left"], "5": [], "6": ["right"],
    "1": ["down", "left"], "2": ["down"], "3": ["down", "right"],
}

DEFAULT_DIR_KEYS = {
    "up": "up", "down": "down", "left": "left", "right": "right",
}


@dataclass
class Character:
    id: str
    name: str
    portrait: Optional[str] = None


@dataclass
class Game:
    id: str
    name: str
    short_name: str
    fightcade_rom: str
    attack_layout: AttackLayout
    characters: List[Character] = field(default_factory=list)
    genre: str = "2D Fighter"
    year: int = 0
    series: str = ""

    @property
    def buttons(self) -> List[str]:
        return LAYOUT_BUTTONS[self.attack_layout]

    @property
    def default_keys(self) -> dict:
        return LAYOUT_DEFAULT_KEYS[self.attack_layout]
