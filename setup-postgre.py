from dotenv import load_dotenv
load_dotenv()

import asyncio
from resources import Database, Namespace

async def main():
    bot = Namespace(redis=None)
    db  = await Database.create(bot) # type: ignore
    
    with open('sql/leagues.sql') as f:
        await db.pool.execute(f.read())

    with open('sql/players.sql') as f:
        await db.pool.execute(f.read())

    with open('sql/blacklist.sql') as f:
        await db.pool.execute(f.read())

    await db.pool.close()
        
asyncio.run(main())