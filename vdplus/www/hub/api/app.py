from dotenv import load_dotenv
load_dotenv()

import os
import logging
logging.basicConfig(level=logging.DEBUG)

import concurrent.futures
import aiohttp
import asyncio
from aiohttp import web

from tty_websocket import tty_websocket_handler
from models.user import User
from pod_manager import PodMan

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
    if request['user'].is_guest:
        username = 'guest'
    else:
        username = request['user'].email

    return web.json_response({
        'response': {
            'username': username,
            'idle_timeout': request['user'].idle_timeout
        },
        'meta': {}
    })

@routes.get('/api/auth')
async def auth(request):
    email = request.query["email"].strip()
    token = User.auth(request, email)

    if is_auto_login(email):
        response = {
            'token': token
        }
    else:
        response = {}

    return web.json_response({
        'response': response,
        'meta': {}
    })

def is_auto_login(email):
    return email == 'guest' or os.getenv('VD_ENV') != 'production' or os.getenv('CI') == 'true'

# Catch-all route to support the SPA routing all non-API requests into index.html
# This enables the standard browser history API that navigates between URLs without page loads.
# This route is only activated if all the above routes are not triggered.
@routes.get('/{path:.*}')
async def root_handler(request):
    return aiohttp.web.FileResponse(SPA_BASE + 'index.html')

async def pod_idle_killer():
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, PodMan.idle_killer_daemon)

async def main():
    app = web.Application()
    app.add_routes([web.get('/ws', tty_websocket_handler)])
    app.router.add_static('/assets/', SPA_BASE)
    app.add_routes(routes)
    await asyncio.gather(
        web._run_app(app, port=8000),
        PodMan.idle_killer_daemon()
    )

asyncio.run(main())

if __name__ == '__main__':
    asyncio.run(main())
