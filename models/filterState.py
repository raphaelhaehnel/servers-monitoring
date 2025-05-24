from dataclasses import dataclass

@dataclass
class FilterState:
    available: bool
    busy: bool
    operational: bool
    type: str