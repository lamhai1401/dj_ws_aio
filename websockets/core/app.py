# from .server import WSApplication
from aiohttp import web
from .views import *

app = web.Application()
app.router.add_get('/ws', WebSocketView)