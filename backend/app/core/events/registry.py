from dataclasses import dataclass


@dataclass
class ModuleMeta:
    name: str
    version: str
    enabled: bool = True


MODULES: list[ModuleMeta] = [
    ModuleMeta(name="habits", version="0.1.0", enabled=True),
    ModuleMeta(name="tasks", version="0.1.0", enabled=True),
    ModuleMeta(name="finance", version="0.1.0", enabled=True),
    ModuleMeta(name="food", version="0.1.0", enabled=False),
    ModuleMeta(name="motivation", version="0.1.0", enabled=True),
]
