import asyncio
import logging
import os
from typing import Literal, TypedDict

from aiohttp import web

from .database import Database
from .files import get_server_info


class DuplicateFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        current_log = (record.module, record.levelno, record.msg)
        if current_log != getattr(self, "last_log", None):
            self.last_log = current_log
            return True
        return False


class ConfigT(TypedDict):
    logging_level: str
    bind_host: str
    bind_port: int
    db_path: str
    watch_path: str
    poll_interval: int


class NotificationItemT(TypedDict):
    type: Literal["updated", "new", "removed"]
    name: str
    port: int


NotificationT = list[NotificationItemT]

config: ConfigT = {
    "logging_level": os.environ.get("MDDW_LOGGING_LEVEL", "INFO"),
    "bind_host": os.environ.get("MDDW_BIND_HOST", "0.0.0.0"),
    "bind_port": int(os.environ.get("MDDW_BIND_PORT", "80")),
    "db_path": os.environ.get("MDDW_DB_PATH", "/data/mc-docker.db"),
    "watch_path": os.environ.get("MDDW_SERVERS_PATH", "/watch"),
    "poll_interval": int(os.environ.get("MDDW_POLL_INTERVAL", "5")),
}

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=config["logging_level"],
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()
logger.addFilter(DuplicateFilter())
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

routes = web.RouteTableDef()

ws_clients: set[web.WebSocketResponse] = set()
db = Database()


async def notify_clients(notification: NotificationT):
    logging.debug("notifying clients...")
    for ws in ws_clients:
        if ws.closed:
            continue
        try:
            await ws.send_json(notification)
        except Exception:
            pass


@routes.get("/all_servers")
async def get_all_servers(request: web.Request):
    logging.debug(f"Client {request.remote} requested all servers")
    return web.json_response(await db.get_all_servers())


# this is used for notifying the client that the maps have changed
@routes.get("/ws")
async def websocket_handler(request: web.Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    logging.info(f"ws connection from {request.remote} open")
    ws_clients.add(ws)

    async for msg in ws:
        # we ignore all other messages
        if msg.type == web.WSMsgType.ERROR:  # type: ignore
            logging.info(f"ws connection closed with exception {ws.exception()}")

    logging.info(f"ws connection from {request.remote} closed")
    ws_clients.remove(ws)

    return ws


async def monitor():
    logging.info("monitoring...")
    while True:
        new_servers = await get_server_info(config["watch_path"])
        stored_servers = await db.get_all_servers()

        if new_servers != stored_servers:
            logging.info("servers changed, updating database")
            await db.override_all_servers(new_servers)

            notification = NotificationT()
            for name, port in new_servers.items():
                if name not in stored_servers:
                    notification.append({"type": "new", "name": name, "port": port})
                elif stored_servers[name] != port:
                    notification.append({"type": "updated", "name": name, "port": port})

            for name, port in stored_servers.items():
                if name not in new_servers:
                    notification.append({"type": "removed", "name": name, "port": port})

            logging.info(f"notification: {notification}")
            await notify_clients(notification)

        await asyncio.sleep(config["poll_interval"])


async def run():
    await db.connect(config["db_path"])

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config["bind_host"], config["bind_port"])
    await site.start()

    await monitor()

    await db.close()


if __name__ == "__main__":
    asyncio.run(run())
