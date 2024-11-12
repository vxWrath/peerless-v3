from __future__ import annotations

import discord
import datetime
import uuid

from functools import cached_property
from pydantic import Field, field_validator
from typing import TYPE_CHECKING, Optional, Any, List, Tuple

import traceback

from .base import BaseModel
from ..exceptions import TeamWithoutRole
from ..namespace import Namespace

if TYPE_CHECKING:
    from ..database import Database
    from .settings import Setting

def _namespace_field(default: Optional[Namespace[str, Any]]=None):
    return Field(default_factory=Namespace if not default else lambda : default)

class League(BaseModel):
    id: int
    blacklisted: bool = False

    premium: Namespace[str, Any] = _namespace_field()

    themes: Namespace[str, List[int] | Namespace[str, Any]] = _namespace_field(Namespace(
        embed_color = [],
        transactions_theme = {"mode": "embed", "data": {}}
    ))

    settings: Namespace[str, int] = _namespace_field()
    channels: Namespace[str, int] = _namespace_field()
    roles: Namespace[str, List[int]] = _namespace_field()
    pings: Namespace[str, str] = _namespace_field()
    alerts: Namespace[str, bool] = _namespace_field()
    statuses: Namespace[str, bool] = _namespace_field()

    teams: Namespace[str, Team] = _namespace_field()
    coaches: Namespace[int, str] = _namespace_field()

    _table: str = "leagues"
    _database: Database

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self._database.bot.get_guild(self.id)

    def get_key_from_role(self, role_id: int) -> Optional[str]:
        for key, role_ids in self.roles.items():
            if role_id in role_ids:
                return key
            
        for key, ping_ids in self.pings.items():
            _, ids = ping_ids.split(':')
            role_ids = [int(x) for x in ids.split('-')]

            if role_id in role_ids:
                return key
            
        return None

    async def add_role(self, key: str, role_id: int, *, sync: Optional[bool]=False) -> None:
        if not self.roles.get(key):
            self.roles[key] = []

        if 'ping' in key:
            ping, ids = self.get_value("pings", key, "2:0").split(':')
            role_ids  = [int(x) for x in ids.split('-')]
            role_ids.append(role_id)
            
            if 0 in role_ids:
                role_ids.remove(0)

            self.pings[key] = f"{ping}:{'-'.join(str(x) for x in role_ids)}"

            if sync:
                await self.update("pings")
        else:
            self.roles[key].append(role_id)

            if sync:
                await self.update("roles")

    async def get_roles(self, key: str) -> List[discord.Role]:
        if not self.guild:
            return []
        
        if (role_ids := self.roles.get(key)):
            pass
        elif (_role_ids := self.pings.get(key)):
            _, ids = _role_ids.split(':')
            role_ids = [int(x) for x in ids.split('-')]
        else:
            return []
        
        roles = {x: self.guild.get_role(x) for x in role_ids if x != 0}
        
        if None in roles.values():
            while None in roles.values():
                role_id = next(x for x, y in roles.items() if not y)
                await self.remove_role(role_id)

            await self.update("roles", "pings")

        return [role for role in roles.values() if role]

    async def get_channel(self, key: str) -> Optional[discord.abc.GuildChannel | discord.Thread]:
        if not self.guild:
            return None
        
        if not (channel_id := self.channels.get(key)):
            return None
        
        channel = self.guild.get_channel_or_thread(channel_id)

        if not channel:
            await self.remove_channel(key, sync=True)
            return None
        return channel

    async def remove_role(self, role_id: int, *, sync: Optional[bool]=False) -> None:
        try:
            category = None
            if (matches := [x for x in self.teams.values() if x.role == role_id]):
                self.teams[matches[0].token].role = None
                category = "teams"
            elif role_id in self.coaches:
                del self.coaches[role_id]
                category = "coaches"
            elif (key := self.get_key_from_role(role_id)):
                category = "pings"

                if 'ping' in key:
                    ping, ids = self.get_value("pings", key, "2:0").split(':')
                    role_ids = [int(x) for x in ids.split('-')]
                    role_ids.remove(role_id)

                    self.pings[key] = f"{ping}:{'-'.join(str(x) for x in role_ids)}"
                else:
                    self.roles[key].remove(role_id)

                    if not len(self.roles[key]):
                        del self.roles[key]

            if category and sync:
                await self.update(category)
        except (KeyError, ValueError) as e:
            traceback.print_exception(type(e), e, e.__traceback__)
            return

    async def remove_channel(self, key: str, *, sync: Optional[bool]=False) -> None:
        if self.channels.get(key):
            del self.channels[key]

            if sync:
                await self.update("channels")

    async def remove_emoji(self, emoji_id: int, *, sync: Optional[bool]=False) -> None:
        matches = [x for x in self.teams.values() if x.emoji == emoji_id]

        if not matches:
            return
        
        team = matches[0]
        self.teams[team.token].emoji = None

        if sync:
            await self.update("teams")

    async def get_team(self, *, token: Optional[str]=None, role_id: Optional[int]=None, emoji_id: Optional[int]=None, sync: Optional[bool]=False) -> Tuple[Optional[Team], Optional[discord.Role], Optional[discord.Emoji]]:
        if not token and not role_id and not emoji_id:
            return None, None, None
        
        if not self.guild:
            return None, None, None
        
        matches = []

        if token:
            matches = [x for x in self.teams.values() if x.token == token]

        if role_id and not matches:
            matches = [x for x in self.teams.values() if x.role == role_id]

        if emoji_id and not emoji_id:
            matches = [x for x in self.teams.values() if x.emoji == emoji_id]

        if not matches:
            return None, None, None
        
        team = matches[0]
        team._league = self

        local_sync = False

        role = emoji = None

        if team.role:
            role = self.guild.get_role(team.role)

            if not role:
                local_sync = True
                await self.remove_role(team.role)

        if team.emoji:
            emoji = self.guild.get_emoji(team.emoji)

            if not emoji:
                local_sync = True
                await self.remove_emoji(team.emoji)

        if sync and local_sync:
            await self.update("teams")

        if not role:
            raise TeamWithoutRole(team)

        return team, role, emoji

    async def update(self, *keys) -> None:
        await self._database.update(self, *keys)

    def get_value(self, category: str, key: str, default: Optional[Any]=None):
        return self[category].get(key, default)

    def get_value_from_setting(self, setting: Setting):
        return self[setting.type.database].get(setting.value, setting.default)

    @field_validator('teams')
    def teams_validator(cls, value: Namespace[str, Namespace[str, Any]]) -> Namespace[str, Team]:
        new_value = Namespace({
            x: Team(**y) for x, y in value.items()
        })
        return new_value
    
    def model_post_init(self, *args):
        for team in self.teams.values():
            team._league = self

class Team(BaseModel):
    token: str = Field(default_factory=lambda : str(uuid.uuid4()))
    role: Optional[int]
    emoji: Optional[int] = None

    role_name: str
    emoji_name: Optional[str] = None

    awards: List[int] = Field(default_factory=list)

    whitelist: List[str] = Field(default_factory=list)
    override: Namespace[str, int] = _namespace_field(Namespace(
        wins = 0,
        losses = 0,
        pf = 0,
        pa = 0
    ))

    seed: Optional[int] = None
    elo: Optional[float] = None
    opponents: List[str] = Field(default_factory=list)

    _league: League

class Player(BaseModel):
    id: int
    blacklisted: bool = False

    leagues: Namespace[int, SubLeague] = Field(default_factory=Namespace)

    _table: str = "players"
    _database: Database

    @field_validator('leagues')
    def leagues_validator(cls, value: Namespace[str, Namespace[str, Any]]) -> Namespace[int, SubLeague]:
        new_value = Namespace({
            int(x): SubLeague(**y) for x, y in value.items()
        })
        return new_value
    
class SubLeague(BaseModel):
    league_id: int
    
    demands: int = 3
    demand_available: Optional[datetime.datetime] = None
    appointed: Optional[datetime.datetime] = None
    waitlisted: Optional[datetime.datetime] = None
    blacklisted: bool = False
    suspension_details: Namespace[str, Optional[datetime.datetime] | bool] = Field(default_factory=lambda : Namespace(
        banned = False,
        until = None
    ))
    contract_details: Namespace[str, Optional[str | int]] = Field(default_factory=lambda : Namespace(
        team_id = None,
        terms = None,
        salary = None,
    ))
    awards: List[Namespace[str, Any]] = Field(default_factory=list)
    
class BlacklistEntry(BaseModel):
    id: int
    reason: str
    moderator_id: int
    date: datetime.datetime

    _table: str = "blacklist"
    _database: Database