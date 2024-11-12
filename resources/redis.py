from __future__ import annotations

import asyncio
import colorlog
import json
import subprocess
import os

from redis.asyncio.client import Redis
from redis import ConnectionError as RedisConnectionError
from typing import TYPE_CHECKING, Type, Self, Optional, Union, Tuple, Dict, Any, Mapping

from .models import BaseModel
from .namespace import Namespace
from .utils import jsonify, unjsonify

if TYPE_CHECKING:
    from .bot import Bot

logger = colorlog.getLogger('bot')

class RedisClient:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.client = Redis(
            decode_responses = True,
            retry_on_timeout = True,
            health_check_interval = 30
        )

        self._ready: asyncio.Future[bool]
        self._ready_has_result = False

    @classmethod
    async def create(cls: Type[Self], bot: Bot) -> Self:
        self = cls(bot)
        self.bot.loop.create_task(self._loop())

        self._ready = bot.loop.create_future()
        await self._ready

        return self
    
    async def _loop(self):
        while True:
            try:
                ping = None
                ping = await asyncio.wait_for(self.client.ping(), timeout=10)

                if not self._ready_has_result:
                    self._ready.set_result(True)
                    self._ready_has_result = True
            except (RedisConnectionError, asyncio.InvalidStateError) as e:
                pass
            
            if ping:
                await asyncio.sleep(30)
                continue

            logger.info('Trying to start redis-server')

            args = ['sudo', 'service', 'redis-server', 'start']
            
            if os.name == 'nt':
                args.insert(0, 'wsl')

            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            process.wait()
            _, stderr = process.communicate()

            if process.returncode == 0:
                logger.info('Started redis-server')
                continue
            
            logger.error(f"Couldn't start the redis-server. Error:\n{stderr.decode().strip()}")
            self._ready.set_exception(RuntimeError("Redis-server not started"))

    async def set(self, *path: Union[str, int], model: Mapping[str, Any], expire: int=60*60) -> Namespace[str, Any]:
        route = ":".join([str(x) for x in path])

        if isinstance(model, BaseModel):
            data = jsonify(model.model_dump(exclude_defaults=True))
        else:
            data = dict(jsonify(model))

        async with self.client.pipeline() as pipe:
            await pipe.set(route, json.dumps(data))
            await pipe.expire(route, expire)
            await pipe.execute()

        return Namespace(data)

    async def get[T](self, *path: Union[str, int], model_cls: Type[T]) -> Optional[T]:
        item = await self.client.get(":".join([str(x) for x in path]))

        if not item:
            return None
        return model_cls(**unjsonify(json.loads(item)))

    async def delete(self, *paths: Union[Tuple[Union[str, int]], str, int]) -> None:
        path_dict: Dict[Optional[int], Any] = {None: []}

        for i, path in enumerate(paths):
            if isinstance(path, (list, tuple)):
                path_dict[i] = path
            else:
                path_dict[None].append(path)

        await self.client.delete(*[":".join(map(str, path)) for path in path_dict.values()])
        return None