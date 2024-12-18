import asyncio
import argparse
import datetime
from os import environ as env

import colorlog
import pytz

from dotenv import load_dotenv
load_dotenv()

from resources import Bot, RedisClient, Database

#parser = argparse.ArgumentParser()
#parser.add_argument('--shard_id', type=int, required=True, help="Shard ID")
#parser.add_argument('--shard_count', type=int, required=True, help="Total number of shards")

class Formatter(colorlog.ColoredFormatter):
    def converter(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp=timestamp, tz=pytz.timezone('US/Central')).timetuple()
    
class DiscordHandler(colorlog.StreamHandler):
    def __init__(self, bot: Bot):
        super().__init__()
        
        self.bot = bot
        
    def handle(self, record) -> bool:
        if record.exc_info:
            self.bot.dispatch("error", "LOGGER", *record.exc_info)
            return True
        else:
            return super().handle(record)
    
async def main():
    token = env[f'TOKEN']
    
    #args = parser.parse_args()
    bot  = Bot([0], 1)

    colors = colorlog.default_log_colors | {"DEBUG": "white"}
    
    bot_handler   = colorlog.StreamHandler()
    bot_formatter = Formatter('%(log_color)s[%(asctime)s][BOT][%(levelname)s] %(message)s', datefmt='%m/%d/%Y %r', log_colors=colors | {"INFO": "bold_purple"})
    bot_logger    = colorlog.getLogger("bot")
    
    bot_handler.setFormatter(bot_formatter)
    bot_logger.addHandler(bot_handler)
    bot_logger.setLevel(colorlog.DEBUG)

    discord_handler   = DiscordHandler(bot)
    discord_formatter = Formatter(' %(log_color)s[%(asctime)s][DISCORD][%(levelname)s] %(message)s', datefmt='%m/%d/%Y %r', log_colors=colors | {"INFO": "black"})
    discord_logger    = colorlog.getLogger("discord")

    discord_handler.setFormatter(discord_formatter)
    discord_logger.addHandler(discord_handler)
    discord_logger.setLevel(colorlog.INFO)

    try:
        async with bot:
            bot.redis = await RedisClient.create(bot)
            bot.database = await Database.create(bot)

            await bot.start(token)
    except asyncio.CancelledError:
        pass
    finally:
        bot_logger.info("Turning Off...")

        await bot.redis.client.aclose()
        await bot.database.pool.close()
        await bot.close()
            
        bot_logger.info("Turned Off")
        
if __name__ == '__main__':
    asyncio.run(main())