"""Governed Cue → Tag → Content memory reconstruction contracts."""
from dataclasses import dataclass, field
from typing import Iterable

@dataclass(frozen=True)
class MemoryNode:
    node_id: str
    cue: str
    tags: tuple[str, ...]
    content_ref: str
    source: str
    active: bool = True

@dataclass(frozen=True)
class Reconstruction:
    cue: str
    selected_nodes: tuple[str, ...]
    tags: tuple[str, ...]
    pruned_nodes: tuple[str, ...] = ()


def reconstruct(cue: str, nodes: Iterable[MemoryNode], tags: Iterable[str]) -> Reconstruction:
    requested = set(tags)
    candidates = [n for n in nodes if n.active and (n.cue == cue or requested.intersection(n.tags))]
    selected = tuple(n.node_id for n in candidates)
    selected_set = set(selected)
    pruned = tuple(n.node_id for n in nodes if n.node_id not in selected_set)
    return Reconstruction(cue=cue, selected_nodes=selected, tags=tuple(sorted(requested)), pruned_nodes=pruned)
