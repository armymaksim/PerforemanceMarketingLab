import asyncio
import sys
import asyncpg
from aiohttp import web
from image_manager.urls import ImageView
from importlib._bootstrap_external import SourceFileLoader


def get_config():
    if len(sys.argv) > 1:
        config = SourceFileLoader("config", sys.argv[1]).load_module()
    else:
        config = SourceFileLoader("config", '/usr/local/etc/image_manager/config.py').load_module()
    from config import dsn
    return dsn


async def init_app(loop):
    app = web.Application(loop=loop)
    app.db = await asyncpg.pool.create_pool(get_config())
    web.view('/', ImageView)
    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(init_app(loop))
def run(port=80):
    web.run_app(app, port=port)

if __name__=='__main__':
    run()
