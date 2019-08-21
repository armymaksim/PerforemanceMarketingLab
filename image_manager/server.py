"""
Инициализация веб сервиса
"""
import asyncio
import sys
import asyncpg
from aiohttp import web
from .view import ImageView
from importlib.machinery import SourceFileLoader
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
        # На крайняк попробуем так (дефолтное хранилище админов)
        config = SourceFileLoader(
            "config",
            '/usr/local/etc/image_manager/config.py'
        ).load_module()
    if hasattr(config, 'dsn'):
        return config.dsn
    raise ValueError('Нет настроек подключения к БД')


async def shutdown(app):
    await app.db.close()
    sys.exit(0)


async def init_app():
    """
        Инициализируем приложение
    :return:
    """
    app = web.Application()
    try:
        app.db = await asyncpg.pool.create_pool(get_config())
    except asyncpg.exceptions.InvalidCatalogNameError:
        raise Exception('DSN сконфигурирован неверно '
                        'или БД не проинициализированна корректно')
    app.router.add_view('/', ImageView)
    app.jinja = env
    app.upload_path = './upload'
    app.add_routes([web.static('/upload', app.upload_path),
                    web.static('/static', './static')])
    app.on_shutdown.append(shutdown)

    return app


loop = asyncio.get_event_loop()
app = loop.run_until_complete(init_app())


def run(port=8080):
    web.run_app(app, port=port, handle_signals=True)
