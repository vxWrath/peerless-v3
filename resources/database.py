from __future__ import annotations

import asyncpg
import colorlog
import json

from typing import TYPE_CHECKING, Type, Self, Optional, List, Tuple, Union, Any, TypeVar
from os import environ as env

if TYPE_CHECKING:
    from .bot import Bot

from .models import League, Player, BlacklistEntry
from .utils import unjsonify, create_subleague

POSTGRE_USER = env["POSTGRE_USER"]
POSTGRE_PASS = env["POSTGRE_PASS"]
POSTGRE_DB   = env["POSTGRE_DB"]

logger = colorlog.getLogger('bot')

async def _init(con):
    await con.set_type_codec(
        'jsonb',
        schema='pg_catalog',
        encoder=json.dumps,
        decoder=json.loads,
        format='text',
    )

type _Model = Union[League, Player, BlacklistEntry]
M = TypeVar('M', League, Player, BlacklistEntry)

class Database:
    def __init__(self, bot: Bot):
        self.bot = bot

        self.redis_client = bot.redis
        self.pool: asyncpg.Pool

    @classmethod
    async def create(cls: Type[Self], bot: Bot) -> Self:
        self = cls(bot)
        self.pool = await asyncpg.create_pool(
            user=POSTGRE_USER,
            password=POSTGRE_PASS,
            database=POSTGRE_DB,
            init=_init,
            command_timeout=300,
            max_size=20,
            min_size=20,
        )

        return self
    
    async def insert(self, model: _Model) -> bool:
        model._database = self
        sql, args = _SQL.insert(model)

        try:
            await self.pool.execute(sql, *args)
            await self.bot.redis.set(model._table.upper(), model.id, model=model)

            return True
        except asyncpg.UniqueViolationError:
            logger.error(f"ID {model.id} already exists in {model._table} table")

        return False
    
    async def update(self, model: _Model, *update_keys) -> bool:
        sql, args = _SQL.update(model, *update_keys)

        await self.pool.execute(sql, *args)
        await self.bot.redis.set(model._table.upper(), model.id, model=model)

        return True

    async def delete(self, model: _Model) -> None:
        sql = _SQL.delete(model)

        await self.pool.execute(sql)
        await self.bot.redis.delete(model._table.upper(), model.id)

    async def get(self, id: int, *, model_cls: Type[M], use_redis: Optional[bool]=True) -> Optional[M]:
        if use_redis:
            model = await self.bot.redis.get(model_cls.__private_attributes__['_table'].default.upper(), id, model_cls=model_cls)
        else:
            model = None

        if not model:
            sql, args = _SQL.fetch(id=id, model_cls=model_cls)
            record = await self.pool.fetchrow(sql, *args)

            if record:
                model = model_cls(**dict(unjsonify(record)))
                await self.bot.redis.set(model._table.upper(), model.id, model=model)

        if model:
            model._database = self
            
        return model

    async def produce_league(self, league_id: int) -> League:
        league = await self.get(league_id, model_cls=League)

        if league is None:
            league = League(id=league_id, _database=self)

        return league
    
    async def produce_player(self, player_id: int, league: Optional[League]=None) -> Player:
        player = await self.get(player_id, model_cls=Player)

        if player is None:
            player = Player(id=player_id, _database=self)

            if league:
                player.leagues[league.id] = create_subleague(league)

            await self.insert(player)
        else:
            if league:
                await self.add_subleague(player, league)

        return player
    
    async def add_subleague(self, player: Player, league: League) -> None:
        if not player.leagues.has(league.id):
            player.leagues[league.id] = create_subleague(league)
            await self.update(player, 'leagues')

class _SQL:
    @staticmethod
    def insert(model: _Model) -> Tuple[str, Any]:
        dump = model.model_dump(exclude_defaults=True)
        sql  = f"INSERT INTO {model._table} ({', '.join(dump.keys())}) VALUES ({', '.join(f'${i}' for i in range(1, len(dump.values())+1))});"
        
        return (sql, dump.values())
    
    @staticmethod
    def update(model: _Model, *keys: str) -> Tuple[str, Any]:
        dump = model.model_dump(include=set(keys) or None)
        dump.pop('id', None)

        sql  = f"UPDATE {model._table} SET {', '.join(f"{key}=${i+1}" for i, key in enumerate(dump.keys()))} WHERE id={model.id};"

        return (sql, dump.values())
    
    @staticmethod
    def delete(model: _Model) -> str:
        return f"DELETE FROM {model._table} WHERE id={model.id}"
    
    @staticmethod
    def fetch(*keys: str, id: Optional[int], model_cls: Type[M]) -> Tuple[str, List[int]]:
        model_keys = model_cls.model_fields.keys()

        for key in keys:
            if key not in model_keys:
                raise ValueError(f"Key {key} is not in model {model_cls.__name__}")

        sql = f"SELECT {', '.join(keys) or '*'} FROM {model_cls.__private_attributes__['_table'].default}"

        if id:
            sql += " WHERE id=$1"
            return (sql, [id])
        return (sql, [])