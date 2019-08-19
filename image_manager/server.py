import asyncio
import sys
import asyncpg
from aiohttp import web
from image_manager.urls import ImageView
from importlib._bootstrap_external import SourceFileLoader
from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(
    loader=PackageLoader('image_manager', 'templates'),
    autoescape=select_autoescape(['html', 'xml']),
    enable_async=True
)
def get_config():
    if len(sys.argv) > 1:
        config = SourceFileLoader("config", sys.argv[1]).load_module()
    else:
        config = SourceFileLoader("config", '/usr/local/etc/image_manager/config.py').load_module()
    from config import dsn
    return dsn


async def init_app(loop):
    app = web.Application()
    try:
        app.db = await asyncpg.pool.create_pool(get_config())
    except asyncpg.exceptions.InvalidCatalogNameError:
        raise Exception('DSN сконфигурирован неверно или БД не проинициализированна корректно')
    app.router.add_view('/', ImageView)
    app.jinja = env
    app.upload_path = './upload'
    app.add_routes([web.static('/upload', './upload'),
                    web.static('/static', './static')])

    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(init_app(loop))
def run(port=8080):
    web.run_app(app, port=port)

if __name__=='__main__':
    run()
