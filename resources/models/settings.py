from __future__ import annotations

import discord

from discord import app_commands, ui
from pydantic import field_validator
from typing import TYPE_CHECKING, Optional, Self, List, Any, Coroutine, Type, Callable

from .base import BaseModel
from .data import League
from ..baseview import BaseView

if TYPE_CHECKING:
    from ..bot import Bot

class Section(BaseModel):
    name: str
    value: str
    emoji: str
    style: str
    categories: List[Category]

class Category(BaseModel):
    name: str
    value: str
    description: str
    emoji: str
    settings: List[Setting]

    _parent: Section

    def to_choice(self) -> app_commands.Choice:
        return app_commands.Choice(name=self.name, value=self.value)

    def to_button(self, callback: Callable[[discord.Interaction[Bot]], None]) -> ui.Button:
        button: ui.Button = ui.Button(label=self.name, emoji=self.emoji, style=getattr(discord.ButtonStyle, self._parent.style))
        button.callback = callback
        
        return button
    
class Setting(BaseModel):
    name: str
    value: str
    default: Any
    type: SettingType
    description: str
    emoji: str
    required: bool

    minimum: Optional[int] = None
    maximum: Optional[int] = None

    options: Optional[List[Option]] = None

    _parent: Category
    
    def to_choice(self) -> app_commands.Choice:
        return app_commands.Choice(name=self.name, value=self.value)
    
class SettingType(BaseModel):
    name: str
    prefix: str
    database: str
    string: Callable[[League, Setting], Coroutine[Any, Any, str]]

    view: Type[BaseView] | None
    
class Option(BaseModel):
    name: str
    description: str
    emoji: str