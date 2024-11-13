from __future__ import annotations

import discord

from discord.ui.select import BaseSelect
from typing import TYPE_CHECKING, Optional, List, Callable, Self, Union, Sequence

from .models import BeforeView, BeforeInteraction
from .utils import respond

if TYPE_CHECKING:
    from .bot import Bot

class BaseView(discord.ui.View):
    children: List[discord.ui.Button[Self] | BaseSelect[Self]] # type: ignore[assignment]
    checks: List[Callable[[Self, discord.Interaction[Bot]], bool]] = []

    def __init__(self, 
            timeout: Optional[int]=120,
            *,
            interaction: Optional[discord.Interaction[Bot]] = None,
            before: Optional[BeforeView] = None
        ):
        super().__init__(timeout=timeout)
        
        self.interaction = interaction
        self.message: Optional[Union[discord.Message, discord.WebhookMessage, discord.InteractionMessage]] = None
        self.before = before

        self.format_custom_ids()

    def __init_subclass__(cls) -> None:
        cls.checks = []
        super().__init_subclass__()

    def format_custom_ids(self) -> None:
        if not self.before or not self.before.components:
            return
        
        keys  = self.before.components.keys()
        names = [(i, self.children[i].callback.callback.__name__) for i in range(len(self.children))] # type: ignore[attr-defined]

        for index, name in names:
            if name in keys:
                self.children[index].custom_id = f"{name}:{self.children[index].custom_id}"

    async def interaction_check(self, interaction: discord.Interaction[Bot]) -> bool: # type: ignore[override]
        interaction.extras['before_interaction'] = None

        if self.before and self.before.components:
            name, *_ = interaction.data['custom_id'].split(':') # type: ignore[index,typeddict-item]
            interaction.extras['before_interaction'] = self.before.components.get(name)

        if self.before and self.before.all_components and not interaction.extras['before_interaction']:
            interaction.extras['before_interaction'] = self.before.all_components

        if not interaction.extras['before_interaction']:
            interaction.extras['before_interaction'] = BeforeInteraction()

        if not await interaction.client.tree.interaction_check(interaction):
            return False
        
        if interaction.channel and interaction.channel.type == discord.ChannelType.private:
            return True
        
        if not self.checks:
            if self.interaction and self.interaction.user != interaction.user:
                await respond(interaction, content="❌ **You don't have permission**", ephemeral=True)
                return False
        else:
            for check in self.checks:
                if not await discord.utils.maybe_coroutine(check, self, interaction): # type: ignore[arg-type]
                    return False

        return True
    
    async def on_timeout(self) -> None:
        if not self.interaction and not self.message:
            return
                
        for child in self.children:
            child.disabled = True
            
        try:
            if self.message:
                await self.message.edit(content="**This message has expired**", view=self)
            elif self.interaction:
                await self.interaction.edit_original_response(content="**This message has expired**", view=self)
        except discord.HTTPException:
            pass

    async def on_error(self, interaction: discord.Interaction[Bot], error: discord.app_commands.AppCommandError, _) -> None: # type: ignore[override]
        return await interaction.client.tree.on_error(interaction, error)
    
    async def cancel_view(self):
        self.stop()

        if not self.interaction:
            return
                
        try:
            await self.interaction.edit_original_response(content="❌ **Canceled**", view=None, embed=None)
        except discord.HTTPException:
            pass
    
    @classmethod
    def check(cls, func: Callable[[Self, discord.Interaction[Bot]], bool]) -> Callable[[Self, discord.Interaction[Bot]], bool]:
        cls.checks.append(func)
        return func
    
class BaseModal(discord.ui.Modal):
    children: Sequence[discord.ui.TextInput[Self]] # type: ignore[assignment]

    def __init__(self, 
            timeout: Optional[int]=120,
            *,
            interaction: Optional[discord.Interaction[Bot]] = None,
            before_interaction: Optional[BeforeInteraction] = None,
            **kwargs
        ):
        super().__init__(timeout=timeout, **kwargs)

        self.interaction = interaction
        self.before_interaction = before_interaction

    async def interaction_check(self, interaction: discord.Interaction[Bot]) -> bool: # type: ignore[override]
        interaction.extras['before_interaction'] = self.before_interaction
        return await interaction.client.tree.interaction_check(interaction)
    
    async def on_timeout(self) -> None:
        if not self.interaction:
            return
            
        try:
            await self.interaction.edit_original_response(content="**This message has expired**", view=self)
        except discord.HTTPException:
            pass

    async def on_error(self, interaction: discord.Interaction[Bot], error: discord.app_commands.AppCommandError) -> None: # type: ignore[override]
        return await interaction.client.tree.on_error(interaction, error)