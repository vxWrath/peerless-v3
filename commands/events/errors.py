"""
This file handles all errors that happen
"""

import datetime
import discord
import colorlog
import sys

from discord import app_commands
from discord.ext import commands
from typing import Dict, Any

from resources import Bot, League, respond, CheckFailure, RolesAlreadyManaged, RolesAlreadyUsed

SETTINGS = {}

logger = colorlog.getLogger('bot')
discord_logger = colorlog.getLogger('discord')

class Errors(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.on_error = self.on_error # type: ignore[method-assign,assignment]
        self.bot.tree.on_error = self.on_app_command_error # type: ignore[assignment]

    @commands.Cog.listener(name="on_error")
    async def on_error(self, event: str, *args, **kwargs):
        if event.upper() == "LOGGER":
            logger.error(f"Handling uncaught error in {event.upper()} event:", exc_info=args)
        else:
            #sys.exc_info()
            logger.error(f"Handling uncaught error in {event.upper()} event:", exc_info=True)

    async def on_app_command_error(self, interaction: discord.Interaction[Bot], error: app_commands.AppCommandError):
        if interaction.guild:
            league: League = interaction.extras.get('league', None) or await interaction.client.database.produce_league(interaction.guild.id)

        kwargs: Dict[str, Any] = {}

        if isinstance(error, app_commands.CommandInvokeError):
            error  = error.__cause__ # type: ignore[assignment]

        if isinstance(error, CheckFailure):
            kwargs = {
                "content": f"❌ **You don't have permission**",
                "ephemeral": True,
            }

        elif isinstance(error, app_commands.CommandOnCooldown):
            retry = discord.utils.utcnow() + datetime.timedelta(seconds=int(error.retry_after))

            kwargs = {
                "content": f"❌ **This command is on cooldown, you may try again {discord.utils.format_dt(retry, "R")}**",
                "ephemeral": True,
            }

        elif isinstance(error, RolesAlreadyUsed):
            roles = error.roles

            if len(roles) == 1:
                role = roles[0]

                kwargs = {
                    "content": f"❌ **{role.mention} is already used in {SETTINGS[league.get_key_from_role(role.id)].name.lower()}**",
                    "ephemeral": True,
                    "allowed_mentions": discord.AllowedMentions.none()
                }
            else:
                kwargs = {
                    "content": f"### ❌ Roles Already Used\n",
                    "ephemeral": True,
                    "allowed_mentions": discord.AllowedMentions.none()
                }

                for role in roles:
                    kwargs['content'] += f"- {role.mention} is already used in `{SETTINGS[league.get_key_from_role(role.id)].name.lower()}`\n"

        if not kwargs:
            kwargs = {
                "content": f"❌ **An unknown error occured**",
                "ephemeral": True,
                "uncaught": True,
            }

        try:
            uncaught = kwargs.pop('uncaught', False)
            await respond(interaction, **kwargs)
        except discord.HTTPException as e:
            if e.code == 50027:
                return
            
            #if self.bot.production:
            #    kwargs.pop('ephemeral', None)
            #    return await interaction.channel.send(**kwargs)

        if uncaught:
            logger.error("Handling uncaught error:", exc_info=(type(error), error, error.__traceback__))
    
    async def handle_error(self):
        pass

async def setup(bot: Bot):
    await bot.add_cog(Errors(bot))