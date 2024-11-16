import colorlog
import discord

from discord import app_commands
from discord.ext import commands
from typing import Literal, Optional

from resources import Bot, BeforeInteraction, developer_only

logger = colorlog.getLogger('bot')

@app_commands.guild_only()
class Sync(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @app_commands.command(
        name='extensions', 
        description='(un)load the cogs & (un)sync the commands', 
        extras={'before': BeforeInteraction(defer=True, ephemerally=True)},
    )
    @app_commands.describe(command="the command to execute", globally="whether to globally (un)sync the commands", guild_str="the guild to (un)sync")
    @app_commands.rename(guild_str='guild')
    @developer_only()
    async def sync(self, interaction: discord.Interaction[Bot], 
                   command: Literal['load', 'sync', 'load & sync', 'unload', 'unsync'], 
                   globally: Optional[Literal["yes", "no"]]="no",
                   guild_str: Optional[str]=None
                ):
        guild: Optional[discord.Guild] = None

        if guild_str and guild_str != "*":
            try:
                int(guild_str)
            except ValueError:
                return await interaction.followup.send(content="Not a valid guild ID", ephemeral=True)
                
            guild = interaction.client.get_guild(int(guild_str))
            
            if not guild:
                return await interaction.followup.send(content="Couldn't find guild", ephemeral=True)
        
        sync_globally = True if globally == "yes" else False
        returnlog = "Extensions "

        guild = guild or interaction.guild
        assert guild

        try:
            for com in command.split(' & '):
                returnlog += f"{com.title()}ed & "
                
                if com == "load":
                    await self.bot.load_extensions()
                
                elif com == "sync":
                    if sync_globally:
                        await self.bot.tree.sync()
                    else:
                        if guild_str != "*":
                            self.bot.tree.copy_global_to(guild=discord.Object(id=guild.id))
                        await self.bot.tree.sync(guild=guild)
                        
                elif command == "unload":
                    await self.bot.unload_extensions()
                    await self.bot.load_extension("commands.extensions")
                    
                elif command == "unsync":
                    await self.bot.unload_extensions()
                    
                    if sync_globally:
                        await self.bot.tree.sync()
                    else:
                        await self.bot.tree.sync(guild=guild)
                        
                    await self.bot.load_extensions()

        except Exception as e:
            await interaction.followup.send(content="❌")
            raise e
        
        logger.info(returnlog[:-3])
        await interaction.followup.send(content="✅")
        
async def setup(bot: Bot):
    cog = Sync(bot)
    
    for command in cog.walk_app_commands():
        if hasattr(command, "callback"):
            command.callback.__name__ = f"{cog.qualified_name.lower()}_{command.callback.__name__}" # type: ignore
            command.guild_only = True
    
    await bot.add_cog(cog)