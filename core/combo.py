from dataclasses import dataclass, field, asdict
from typing import List, Optional
import uuid
from datetime import datetime


@dataclass
class ComboStep:
    direction: str = "5"      # numpad 1-9, "5" = neutral
    attacks: List[str] = field(default_factory=list)
    hold: bool = False
    delay_ms: int = 0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_notation(self) -> str:
        parts = []
        if self.direction != "5":
            parts.append(self.direction)
        parts.extend(self.attacks)
        result = "+".join(parts) if parts else "5"
        if self.hold:
            result = f"[{result}]"
        return result


@dataclass
class Combo:
    name: str
    character_id: str
    game_id: str
    steps: List[ComboStep] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    hotkey: Optional[dict] = None   # e.g. {"type": "keyboard", "key": "F1"}
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def notation(self) -> str:
        return ", ".join(s.to_notation() for s in self.steps)

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d):
        steps = [ComboStep.from_dict(s) for s in d.pop("steps", [])]
        combo = cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
        combo.steps = steps
        return combo
