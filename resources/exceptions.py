from __future__ import annotations

import discord
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .models import Team

class BotException(Exception):
    """Base exception for all bot errors"""
    pass

class CheckFailure(discord.app_commands.CheckFailure):
    def __init__(self, check: str):
        self.check = check

class RolesNotAssignable(BotException):
    def __init__(self, roles: List[discord.Role]):
        self.roles = roles
        
class RolesAlreadyManaged(BotException):
    def __init__(self, roles: List[discord.Role]):
        self.roles = roles
        
class RolesAlreadyUsed(BotException):
    def __init__(self, roles: List[discord.Role]):
        self.roles = roles

class NotEnoughTeams(BotException):
    def __init__(self, required: int):
        self.required = required

class TeamWithoutRole(BotException):
    def __init__(self, team: Team):
        self.team = team