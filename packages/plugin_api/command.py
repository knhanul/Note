"""Command data structures for Note2 plugin API."""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Command:
    id: str
    title: str
    handler: Callable[..., object]
    description: Optional[str] = None
