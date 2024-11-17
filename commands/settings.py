"""
This file contains the following commands:
    /settings
    /searchsettings
"""

from __future__ import annotations

import discord

from discord.ext import commands
from discord import app_commands, ui
from typing import Optional, List

from resources import (
    Bot,
    BeforeInteraction,
    get_matches,
    CATEGORIES,
    Category,
    SETTINGS
)

async def category_auto(_: discord.Interaction[Bot], current: str) -> List[app_commands.Choice]:
    if not current:
        return [x.to_choice() for x in CATEGORIES][:25]

    names   = [x.name for x in CATEGORIES]
    matches = get_matches(current, names, limit=25)

    return [
        CATEGORIES[names.index(x)].to_choice() 
        for x, y in matches
        if y > max(10, min(85, len(current) * 15))
    ]

async def setting_auto(interaction: discord.Interaction[Bot], current: str) -> List[app_commands.Choice]:
    category: List[str] = [x["value"] for x in interaction.data['options'] if x['name'] == 'category'] # type: ignore

    if category:
        category: List[Category] = [x for x in CATEGORIES if category[0].lower() == x.name.lower()] # type: ignore

    if category:
        settings = category[0].settings
    else:
        settings = list(SETTINGS.values())

    if not current:
        return [x.to_choice() for x in settings][:25]
    
    names = [x.name for x in settings]
    matches = get_matches(current, names, limit=25)

    return [
        settings[names.index(x)].to_choice()
        for x, y in matches
        if y > max(10, min(85, len(current) * 15))
    ]

class Settings(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @app_commands.command(
        name="settings", 
        description="manage league variables",
        extras={'before': BeforeInteraction(ephemerally=True)}, # Commands get league data automatically
    )
    @app_commands.describe(category="The category you want to edit/view", setting="The setting you want to change")
    @app_commands.autocomplete(category=category_auto, setting=setting_auto)
    async def settings(self, interaction: discord.Interaction[Bot],
        category: Optional[str] = None,
        setting: Optional[str] = None
    ):
        pass

    @app_commands.command(
        name="searchsettings", 
        description="search for the setting you need",
        extras={'before': BeforeInteraction(defer=True, ephemerally=True)}, # Commands get league data automatically
    )
    @app_commands.describe(query="what your looking for")
    async def search(self, interaction: discord.Interaction[Bot],
        query: str
    ):
        pass
        
async def setup(bot: Bot):
    cog = Settings(bot)
    
    for command in cog.walk_app_commands():
        if hasattr(command, "callback"):
            command.callback.__name__ = f"{cog.qualified_name.lower()}_{command.callback.__name__}" # type: ignore
            command.guild_only = True
    
    await bot.add_cog(cog)