import os
import asyncio
import logging
import datetime
import time
import concurrent.futures

from models.user import User
from k8s import k8s_create_pod, k8s_delete_pod

GOTTY_PORT = os.getenv('GOTTY_PORT', '9000')
THROTTLE = 5
PROTOCOL_FOR_TTY_INPUT = '1'
PROTOCOL_FOR_TTY_PING = '2'

class PodMan:
    def __init__(self, user):
        self.user = user

    def using_local_gotty():
        if os.getenv("USE_REMOTE_K8S") == "true":
            return False
        if os.getenv("VD_ENV") == "dev" or os.getenv("CI") == "true":
            return True
        return False

    async def get_address(self):
        if self.user.current_pod_ip != '' and self.user.current_pod_ip != None:
            return self.reconnect()
        else:
            if PodMan.using_local_gotty():
                ip = "127.0.0.1"
            else:
                ip = k8s_create_pod(self.user)
            if ip:
                self.user.current_pod_ip = ip
                self.user.save()
                url = self.url()
                logging.debug(f"Created pod for user {self.user.id} at: {url}")
                return url
            else:
                logging.error(f"Couldn't create container for user: {self.user.id}")
                return False

    def url(self):
        return f'http://{self.user.current_pod_ip}:{GOTTY_PORT}'

    def reconnect(self):
        logging.debug(f"Reconnecting to user {self.user.id}'s existing pod: {self.url()}")
        return self.url()

    def delete(self):
        timeout = self.user.idle_timeout
        message = f"Idle timeout ({timeout}), deleting pod for user: {self.user.id}"
        logging.info(message)
        self.user.current_pod_ip = ''
        self.user.save()
        if PodMan.using_local_gotty():
            return
        k8s_delete_pod(self.user)

    async def idle_timestamp(self, data):
        if not data.startswith(PROTOCOL_FOR_TTY_INPUT):
            return

        elapsed = time.time() - self.user.last_input.timestamp()
        if elapsed < THROTTLE:
            return

        await self.save_input_timestamp()

    async def save_input_timestamp(self):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, self._save_input_timestamp)

    # Save timestamp to DB because a user could reconnect to a session via a different
    # hub container instance to this one.
    def _save_input_timestamp(self):
        logging.debug("Timestamping user's last input record")
        self.user.last_input = datetime.datetime.now()
        self.user.save()

    async def idle_killer_daemon():
        try:
            await PodMan.idle_killer_loop()
        except RuntimeError:
            return
        except Exception as e:
            logging.exception(e)
        finally:
            await PodMan.idle_killer_daemon()

    async def idle_killer_loop():
        while True:
            await asyncio.sleep(1)
            users = User.select().where(User.current_pod_ip != '')
            for user in users:
                podman = PodMan(user)
                podman.idle_killer()

    def idle_killer(self):
        if self.user.last_input is None:
            return
        if time.time() - self.user.last_input.timestamp() > self.user.idle_timeout:
            self.delete()
