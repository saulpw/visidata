from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.DEBUG)

import aiohttp
import asyncio
from aiohttp import web

from tty_websocket import tty_websocket_handler
from models.user import User

SPA_BASE = '../spa/dist/'

routes = web.RouteTableDef()

def authenticate(func):
    def wrapper(request):
        try:
            _scheme, token = request.headers['Authorization'].strip().split(' ')
        except KeyError:
            raise web.HTTPUnauthorized(reason='Missing authorization header',)
        except ValueError:
            raise web.HTTPForbidden(reason='Invalid authorization header',)

        user = User.select().where(User.token == token)
        if user.exists():
            request['user'] = user.get()
        else:
            raise web.HTTPForbidden(reason='Unauthorized')

        return func(request)
    return wrapper

@routes.get('/api/account')
@authenticate
async def user(request):
    return web.json_response({
        'response': {
            'email': request['user'].email
        },
        'meta': {}
    })

@routes.get('/api/auth')
async def auth(request):
    email = request.query["email"]
    return web.json_response({
        'response': {
            'magic_link': User.auth(request, email)
        },
        'meta': {}
    })

# Catch-all route to support the SPA routing all non-API requests into index.html
# This enables the standard browser history API that navigates between URLs without page loads.
# This route is only activated if all the above routes are not triggered.
@routes.get('/{path:.*}')
async def root_handler(request):
    return aiohttp.web.FileResponse(SPA_BASE + 'index.html')

def create_app():
    app = web.Application()
    app.add_routes([web.get('/ws', tty_websocket_handler)])
    app.router.add_static('/assets/', SPA_BASE)
    app.add_routes(routes)
    web.run_app(app, port=8000)
    return app

if __name__ == '__main__':
    create_app()
