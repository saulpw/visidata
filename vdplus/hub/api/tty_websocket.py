import asyncio
import aiohttp
import logging
from aiohttp import web

from models.user import User
from pod_manager import PodMan

MSGCODE_AUTH = "6"

async def tty_websocket_handler(request):
    logging.debug("Websocket handler triggered")
    queue = asyncio.Queue()

    # Inbound from the browser
    inbound = web.WebSocketResponse()
    await inbound.prepare(request)
    user = await auth_connection(inbound)
    if user:
        await inbound.send_str(MSGCODE_AUTH + "auth SUCCESS")
        podman = PodMan(user)
        await podman.save_input_timestamp()
    else:
        await inbound.send_str(MSGCODE_AUTH + "auth FAIL")
        return inbound

    try:
        await manage_connection(queue, inbound, podman)
    except Exception as e:
        podman.delete()
        raise e

async def manage_connection(queue, inbound, podman):
    logging.debug(f"Handling incoming websocket for user ID: {podman.user.id}")
    inbound_task = asyncio.create_task(inbound_socket(inbound, queue))

    vd_container_address = await podman.get_address()
    if not vd_container_address:
        return inbound

    # Outbound to dedicated VisiData container
    session = aiohttp.ClientSession()
    logging.debug(f"Attempting to open outbound socket to: {vd_container_address}")
    outbound = await session.ws_connect(vd_container_address + "/ws")
    outbound_task = asyncio.create_task(outbound_socket(outbound, queue, podman))

    await connect_browser_to_pod(inbound, outbound, queue, podman)

    inbound_task.cancel()
    outbound_task.cancel()

# This loop is paramount in providing low latency UI feedback.
# Anything that happens in here should be low on IO blocking and CPU work.
async def connect_browser_to_pod(inbound, outbound, queue, podman):
    while True:
        source, data = await queue.get()
        if source == 'inbound':
            await podman.idle_timestamp(data)
            await outbound.send_str(data)
        if source == 'outbound':
            if data == 'CLOSE':
                inbound_close(inbound)
                podman.delete()
                break
            await inbound.send_str(data)

async def auth_connection(socket):
    async for msg in socket:
        if msg.type == aiohttp.WSMsgType.TEXT:
            user = User.select().where(User.token == msg.data)
            if user.exists():
                return user.get()
            else:
                return False
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logging.error('Inbound webscoket closed with exception %s' % socket.exception())
            return False
    return False

async def inbound_socket(inbound, queue):
    async for msg in inbound:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await inbound_close(inbound)
            else:
                queue.put_nowait(['inbound', msg.data])
        elif msg.type == aiohttp.WSMsgType.ERROR:
            await inbound_close(inbound)
            logging.error('Inbound websocket closed with exception %s' % inbound.exception())
    await inbound_close(inbound)

async def inbound_close(inbound):
    await inbound.close()

async def outbound_socket(outbound, queue, podman):
    while True:
        msg = await outbound.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await outbound_close(outbound, podman, queue)
                break
            else:
                queue.put_nowait(['outbound', msg.data])
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            await outbound_close(outbound, podman, queue)
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            await outbound_close(outbound, podman, queue)
            break

async def outbound_close(outbound, podman, queue):
    queue.put_nowait(['outbound', 'CLOSE'])
    podman.delete()
    await outbound.close()
