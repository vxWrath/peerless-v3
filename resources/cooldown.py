from __future__ import annotations

import time
import uuid

from discord import Interaction
from discord.app_commands import Command, ContextMenu, CommandOnCooldown
from discord.utils import MISSING, maybe_coroutine
from pydantic import model_validator
from typing import TYPE_CHECKING, Optional, Any, Literal, Callable, Union, Coroutine, TypeVar, Hashable

from .models import BaseModel

T = TypeVar('T')

if TYPE_CHECKING:
    from .bot import Bot

    CooldownFunction = Callable[[Interaction[Bot]], Union[T, Coroutine[Any, Any, T]]]
    ChangeableCooldownFunction = Callable[[Interaction[Bot], int, int], Union[T, Coroutine[Any, Any, T]]]

class Cooldown(BaseModel):
    rate: int # attempts possible
    per: int # how many attemps every certain amount of time

    window: float = 0.0 # time of first attempt
    tokens: Optional[int] = None # attempts left
    last: float = 0.0 # time of latest attempt

    @model_validator(mode='after')
    def after(self) -> Any:
        if self.tokens is None:
            self.tokens = self.rate

    def get_tokens(self, current_time: Optional[float]=None) -> int:
        assert self.tokens

        current_time = current_time or time.time()
        tokens_left  = max(self.tokens, 0)

        if current_time > self.window + self.per:
            tokens_left = self.rate

        return tokens_left
    
    def get_retry_after(self, current_time: Optional[float]=None) -> float:
        current_time = current_time or time.time()
        tokens = self.get_tokens(current_time)

        if tokens == 0:
            return self.per - (current_time - self.window)
        return 0.0
    
    def update_rate_limit(self, current_time: Optional[float]=None, *, tokens: int=1) -> Optional[float]:
        current_time = current_time or time.time()
        self.last = current_time

        self.tokens = self.get_tokens(current_time)

        if self.tokens == self.rate:
            self.window = current_time

        self.tokens -= tokens

        if self.tokens < 0:
            return self.per - (current_time - self.window)
        return None

class CooldownMapping:
    def __init__(self, key: CooldownFunction[Hashable], factory: CooldownFunction[Optional[Cooldown]], rate: int, per: int):
        self.map_id = str(uuid.uuid4())

        self.key = key
        self.factory = factory

        self.rate = rate
        self.per = per

    async def add_bucket(self, interaction: Interaction[Bot]) -> Optional[Cooldown]:
        key = str(await maybe_coroutine(self.key, interaction))
        bucket = await maybe_coroutine(self.factory, interaction)

        if bucket is not None:
            await interaction.client.redis.set("COOLDOWN", self.map_id, key, model=bucket, expire=self.per)
        return bucket

    async def get_bucket(self, interaction: Interaction[Bot]) -> Optional[Cooldown]:
        key = str(await maybe_coroutine(self.key, interaction))
        bucket = await interaction.client.redis.get("COOLDOWN", self.map_id, key, model_cls=Cooldown)

        if not bucket:
            bucket = await maybe_coroutine(self.factory, interaction)
            if bucket:
                await interaction.client.redis.set("COOLDOWN", self.map_id, key, model=bucket, expire=self.per)

        return bucket
    
    async def predicate(self, interaction: Interaction[Bot]) -> Literal[True]:
        bucket = await self.get_bucket(interaction)

        if bucket is None:
            return True
        
        retry_after = bucket.update_rate_limit(interaction.created_at.timestamp())
        await interaction.client.redis.set("COOLDOWN", self.map_id, str(await maybe_coroutine(self.key, interaction)), model=bucket, expire=self.per)

        if retry_after is None:
            return True

        raise CommandOnCooldown(bucket, retry_after) # type: ignore[arg-type]
    
class ChangeableCooldownMapping(CooldownMapping):
    def __init__(self, key: CooldownFunction[Hashable], factory: ChangeableCooldownFunction[Optional[Cooldown]], rate: int, per: int):
        self.map_id = str(uuid.uuid4())

        self.key = key
        self.factory = factory # type: ignore[assignment]

        self.rate = rate
        self.per = per

    async def add_bucket(self, interaction: Interaction[Bot], rate: int, per: int): # type: ignore[override]
        key = str(await maybe_coroutine(self.key, interaction))

        if interaction.client.redis.get("COOLDOWN", self.map_id, key, model_cls=dict):
            return

        bucket: Optional[Cooldown] = await maybe_coroutine(self.factory, interaction, rate, per) # type: ignore[call-arg]

        if bucket is not None:
            await interaction.client.redis.set("COOLDOWN", self.map_id, key, model=bucket, expire=per)
    
def cooldown_check(mapping: CooldownMapping):
    def decorator(func):
        if isinstance(func, (Command, ContextMenu)):
            func.checks.append(mapping.predicate)
        else:
            if not hasattr(func, '__discord_app_commands_checks__'):
                func.__discord_app_commands_checks__ = []

            func.__discord_app_commands_checks__.append(mapping.predicate)
            
        func.extras['cooldown'] = mapping
        return func

    return decorator

def cooldown(rate: int, per: int, *, key: Optional[CooldownFunction[Hashable]]=MISSING):
    if key is MISSING:
        key_func = lambda interaction: interaction.user.id
    elif key is None:
        key_func = lambda interaction: None
    else:
        key_func = key

    factory = lambda i: Cooldown(rate=rate, per=per)
    return cooldown_check(CooldownMapping(key_func, factory, rate, per))

def changeable_cooldown(rate: int, per: int, *, key: Optional[CooldownFunction[Hashable]]=MISSING):
    key_func: CooldownFunction[int | None | Hashable]

    if key is MISSING:
        key_func = lambda i: i.user.id
    elif key is None:
        key_func = lambda i: None
    else:
        key_func = key

    factory: Callable[[Interaction[Bot], int, int], Cooldown] = lambda i, r, p: Cooldown(rate=r, per=p)
    return cooldown_check(ChangeableCooldownMapping(key_func, factory, rate, per))