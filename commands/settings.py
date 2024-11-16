"""
This file contains the following commands:
    /settings
    /searchsettings
"""

from __future__ import annotations

import discord

from discord.ext import commands
from discord import app_commands, ui
from typing import Optional

from resources import (
    Bot,
    BeforeInteraction
)

class Settings(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @app_commands.command(
        name="settings", 
        description="manage league variables",
        extras={'before': BeforeInteraction(ephemerally=True)}, # Commands get league data automatically
    )
    @app_commands.describe(category="The category you want to edit/view", setting="The setting you want to change")
    #@app_commands.autocomplete(category=category_auto, setting=setting_auto)
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