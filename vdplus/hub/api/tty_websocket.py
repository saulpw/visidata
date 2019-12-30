import os
import asyncio
import aiohttp
from aiohttp import web
import logging

from models.user import User
from k8s import create_pod, delete_pod

MSGCODE_AUTH = "6"
LOCAL_GOTTY_INSTANCE = 'http://localhost:8181'
LIVE_GOTTY_PORT = '9000'

def using_local_gotty():
    if os.getenv("USE_REMOTE_K8S") == "true":
        return False
    if os.getenv("VD_ENV") == "dev" or os.getenv("CI") == "true":
        return True
    return False

async def tty_websocket_handler(request):
    logging.debug("Websocket handler triggered")
    queue = asyncio.Queue()

    # Inbound from the browser
    inbound = web.WebSocketResponse()
    await inbound.prepare(request)
    user = await auth_connection(inbound)
    if user:
        await inbound.send_str(MSGCODE_AUTH + "auth SUCCESS")
    else:
        await inbound.send_str(MSGCODE_AUTH + "auth FAIL")
        return inbound

    try:
        await manage_connection(queue, inbound, user)
    except Exception as e:
        delete_vd_container(user)
        raise e

def delete_vd_container(user):
    if not using_local_gotty():
        delete_pod(str(user.get().id))

async def manage_connection(queue, inbound, user):
    logging.debug("Handling incoming websocket for user ID: " + str(user.get().id))
    inbound_task = asyncio.create_task(inbound_socket(inbound, queue, user))

    vd_container_address = await get_vd_container_address(user)
    if not vd_container_address:
        return inbound

    # Outbound to dedicated VisiData container
    session = aiohttp.ClientSession()
    logging.debug("Attempting to open outbound socket to: " + vd_container_address)
    outbound = await session.ws_connect(vd_container_address + "/ws")
    outbound_task = asyncio.create_task(outbound_socket(outbound, queue, user))

    while True:
        source, data = await queue.get()
        if source == 'inbound':
            await outbound.send_str(data)
        if source == 'outbound':
            await inbound.send_str(data)

    inbound_task.cancel()
    outbound_task.cancel()

async def get_vd_container_address(user):
    if using_local_gotty():
        # A standard local GoTTY instance
        return LOCAL_GOTTY_INSTANCE
    ip = create_pod(user)
    if ip:
        return 'http://' + ip + ':' + LIVE_GOTTY_PORT
    else:
        return False

async def auth_connection(socket):
    async for msg in socket:
        if msg.type == aiohttp.WSMsgType.TEXT:
            user = User.select().where(User.token == msg.data)
            if user.exists():
                return user
            else:
                return False
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logging.error('Inbound webscoket closed with exception %s' % socket.exception())
            return False
    return False

async def inbound_socket(inbound, queue, user: User):
    async for msg in inbound:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await inbound_close(inbound, user)
            else:
                queue.put_nowait(['inbound', msg.data])
        elif msg.type == aiohttp.WSMsgType.ERROR:
            await inbound_close(inbound, user)
            logging.error('Inbound webscoket closed with exception %s' % inbound.exception())
    await inbound_close(inbound, user)

async def inbound_close(inbound, user):
    delete_vd_container(user)
    await inbound.close()

async def outbound_socket(outbound, queue, user: User):
    while True:
        msg = await outbound.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await outbound_close(outbound, user)
                break
            else:
                queue.put_nowait(['outbound', msg.data])
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            await outbound_close(outbound, user)
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            await outbound_close(outbound, user)
            break

async def outbound_close(outbound, user):
    delete_vd_container(user)
    await outbound.close()
