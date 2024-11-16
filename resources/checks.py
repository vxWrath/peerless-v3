from __future__ import annotations

import discord

from typing import TYPE_CHECKING, Literal
from .exceptions import CheckFailure

if TYPE_CHECKING:
    from .bot import Bot

def is_developer(user: discord.User | discord.Member) -> bool:
    ids = [
        1104883688279384156, # godmadewrath
        450136921327271946,  # wrath
        1030125659781079130, # veemills
        1010231134048759900, # zuc
        875219288502452254,  # kibs
        976237984766648370,  # sal
    ]
    
    return user.id in ids

def developer_only():
    async def pred(interaction: discord.Interaction[Bot]) -> Literal[True]:
        if is_developer(interaction.user):
            return True
        raise CheckFailure("developer_only")
        
    return discord.app_commands.check(pred)

def guild_owner_only():
    def pred(interaction: discord.Interaction[Bot]) -> Literal[True]:
        if interaction.guild and interaction.user.id != interaction.guild.owner_id:
            raise CheckFailure("guild_owner_only")
        return True
        
    return discord.app_commands.check(pred)