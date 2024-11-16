import asyncio
import colorlog
import datetime
import discord
import os
import sys

from discord.app_commands import Command, CommandTree
from discord.ext import commands
from typing import List

intents = discord.Intents.none()
intents.guilds  = True
intents.emojis  = True
intents.members = True

member_cache_flags = discord.MemberCacheFlags().none()
member_cache_flags.joined = True

from .database import Database
from .redis import RedisClient

class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix = [],
            tree_cls = AppCommandTree,
            intents = intents,
            member_cache_flags = member_cache_flags,
            max_messages = None,
            chunk_guilds_at_startup = False
        )

        self.redis: RedisClient
        self.database: Database

    async def setup_hook(self) -> None:
        await self.load_extensions()

        logger = colorlog.getLogger('bot')

        assert self.user
        
        logger.info(f"Logged in - {self.user.name} ({self.application_id})")
        logger.info(f"Loaded {len([x for x in self.tree.walk_commands() if isinstance(x, Command)])} Commands")

    async def load_extensions(self) -> None:
        self._cogs_: List[str] = []
        
        for cog in self._cogs_:
            try:
                await self.reload_extension(cog)
            except commands.ExtensionNotLoaded:
                await self.load_extension(cog)
        
        dont_load = []
        for dir_, _, files in os.walk('./commands'):
            for file in files:
                if not file.endswith('.py') or file in dont_load:
                    continue
                
                self._cogs_.append(dir_[2:].replace("\\" if sys.platform == 'win32' else '/', ".") + f".{file[:-3]}")
                
                try:
                    await self.reload_extension(self._cogs_[-1])
                except commands.ExtensionNotLoaded:
                    await self.load_extension(self._cogs_[-1])

        return None
                    
    async def unload_extensions(self) -> None:
        for i in range(0, len(self._cogs_)):
            try:
                await self.unload_extension(self._cogs_[i])
            except commands.ExtensionNotLoaded:
                pass

        return None

class AppCommandTree(CommandTree[Bot]):
    pass