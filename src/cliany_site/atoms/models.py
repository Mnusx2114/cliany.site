from dataclasses import dataclass


@dataclass
class AtomParameter:
    name: str
    description: str
    default: str
    required: bool


@dataclass
class AtomCommand:
    atom_id: str
    name: str
    description: str
    domain: str
    parameters: list[AtomParameter]
    actions: list[dict]
    created_at: str
    source_workflow: str
