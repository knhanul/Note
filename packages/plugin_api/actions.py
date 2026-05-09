"""Action data structures for Note2 plugin API."""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class MenuAction:
    id: str
    title: str
    command_id: Optional[str] = None
    location: Optional[str] = None


@dataclass(frozen=True)
class DocumentAction:
    id: str
    title: str
    handler: Optional[Callable[..., object]] = None


@dataclass(frozen=True)
class SidebarPanel:
    id: str
    title: str
    component: Optional[object] = None
    factory: Optional[Callable[..., object]] = None
