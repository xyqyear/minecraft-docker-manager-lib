import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aiofiles.os as aioos

from .docker.compose_file import ComposeFile
from .docker.compose_models import Ports
from .docker.manager import ComposeManager
from .utils import async_rmtree

player_message_pattern = re.compile(
    r"\]: (?:\[Not Secure\] )?<(?P<player>.*?)> (?P<message>.*)"
)


@dataclass
class LogType:
    content: str
    pointer: int


@dataclass
class MCServerInfo:
    name: str
    game_version: str
    game_port: str | int
    rcon_port: str | int


@dataclass
class MCPlayerMessage:
    player: str
    message: str


class MCInstance:
    def __init__(self, servers_path: str | Path, name: str) -> None:
        self._servers_path = Path(servers_path)
        self._name = name

    def get_name(self) -> str:
        return self._name

    @staticmethod
    async def get_compose_file_path_for_server(
        _servers_path: str | Path, server_name: str
    ) -> Path | None:
        server_path = Path(_servers_path) / server_name
        if await aioos.path.exists(server_path / "docker-compose.yml"):
            return server_path / "docker-compose.yml"
        if await aioos.path.exists(server_path / "docker-compose.yaml"):
            return server_path / "docker-compose.yaml"
        return None

    async def get_compose_file_path(self) -> Path | None:
        return await self.get_compose_file_path_for_server(
            self._servers_path, self._name
        )

    async def get_compose_manager(self) -> ComposeManager:
        compose_file_path = await self.get_compose_file_path()
        if compose_file_path is None:
            raise FileNotFoundError(
                f"Could not find docker-compose file for server {self._name}"
            )
        return ComposeManager(compose_file_path)

    def verify_compose_obj(self, compose_obj: ComposeFile) -> bool:
        """
        a docker minecraft server must meet the following requirements:
        - have a docker-compose file
        - the docker-compose file must have a service named "mc"
            - container name must be "mc-<self._name>"
            - this service must use the image "itzg/minecraft-server"
            - this service must have a port mapping to 25565
        """
        if compose_obj.services is None:  # type: ignore
            return False
        for service_name, service in compose_obj.services.items():  # type: ignore
            if service_name != "mc":
                continue
            if service.container_name != f"mc-{self._name}":
                continue
            if service.image is None or not service.image.startswith(
                "itzg/minecraft-server"
            ):
                continue
            if service.ports is None:
                continue
            for port in service.ports:
                if isinstance(port, Ports):
                    if str(port.target) == "25565":
                        return True
        return False

    async def get_compose_obj(self) -> ComposeFile:
        compose_obj = await ComposeFile.async_from_file(self._servers_path)

        if self.verify_compose_obj(compose_obj):
            return compose_obj

        raise FileNotFoundError(
            f"Could not find valid docker-compose file for server {self._name}"
        )

    def _get_log_path(self) -> Path:
        return self._servers_path / self._name / "data" / "logs" / "latest.log"

    async def get_log_file_end_pointer(self) -> int:
        async with aiofiles.open(self._get_log_path(), mode="r", encoding="utf8") as f:
            await f.seek(0, 2)
            return await f.tell()

    async def get_logs_from_file(self, start: int = 0) -> LogType:
        """
        if start is negative, it will read start bytes from the end of the file
        if start is positive and no greater than the file size, it will read start bytes from the specified position
        if start is greater than the file size, it will read from the beginning of the file
        raises:
            FileNotFoundError: if the log file does not exist
        """
        async with aiofiles.open(self._get_log_path(), mode="r", encoding="utf8") as f:
            await f.seek(0, 2)
            file_size = await f.tell()
            if start < 0:
                start = file_size + start
                if start < 0:
                    start = 0
            elif start > file_size:
                start = 0
            await f.seek(start)
            log = await f.read()
            return LogType(content=log, pointer=await f.tell())

    def _parse_player_messages_from_log(self, log: str) -> list[MCPlayerMessage]:
        return [
            MCPlayerMessage(
                player=match.group("player"), message=match.group("message")
            )
            for match in player_message_pattern.finditer(log)
        ]

    async def get_player_messages_from_log(
        self, start: int = 0
    ) -> tuple[list[MCPlayerMessage], int]:
        log = await self.get_logs_from_file(start)
        return self._parse_player_messages_from_log(log.content), log.pointer

    async def get_logs_from_docker(self, tail: int = 1000) -> str:
        compose_manager = await self.get_compose_manager()
        return await compose_manager.logs(tail)

    async def create(self, compose_obj: ComposeFile) -> None:
        """
        create a new directory for the server and write the compose file to it
        it also creates a data directory for the server
        """
        if not self.verify_compose_obj(compose_obj):
            raise ValueError("Invalid compose file")

        await aioos.makedirs(self._servers_path / self._name, exist_ok=True)
        if await self.get_compose_file_path() is not None:
            raise FileExistsError(
                f"docker-compose file already exists for server {self._name}"
            )
        compose_file_path = self._servers_path / self._name / "docker-compose.yml"
        await compose_obj.async_to_file(compose_file_path)
        await aioos.makedirs(self._servers_path / self._name / "data", exist_ok=True)

    async def update_compose_file(self, compose_obj: ComposeFile) -> None:
        if not self.verify_compose_obj(compose_obj):
            raise ValueError("Invalid compose file")

        compose_file_path = await self.get_compose_file_path()
        if compose_file_path is None:
            raise FileNotFoundError(
                f"Could not find docker-compose file for server {self._name}"
            )
        await compose_obj.async_to_file(compose_file_path)

    async def remove(self) -> None:
        compose_manager = await self.get_compose_manager()
        if await compose_manager.running():
            raise RuntimeError(f"Cannot remove server {self._name} while it is running")
        if await compose_manager.created():
            raise RuntimeError(f"Cannot remove server {self._name} while it is created")
        compose_file_path = compose_manager.compose_file_path
        await async_rmtree(compose_file_path.parent)

    async def up(self) -> None:
        compose_manager = await self.get_compose_manager()
        await compose_manager.up_detached()

    async def down(self) -> None:
        compose_manager = await self.get_compose_manager()
        await compose_manager.down()

    async def start(self) -> None:
        compose_manager = await self.get_compose_manager()
        await compose_manager.run_command("start")

    async def stop(self) -> None:
        compose_manager = await self.get_compose_manager()
        await compose_manager.run_command("stop")

    async def restart(self) -> None:
        compose_manager = await self.get_compose_manager()
        await compose_manager.restart()

    async def exists(self) -> bool:
        """
        exists means that the server has a compose file
        """
        compose_file_path = await self.get_compose_file_path()
        return compose_file_path is not None

    async def created(self) -> bool:
        """
        created means that the container has been created but it is not running
        """
        compose_manager = await self.get_compose_manager()
        return await compose_manager.created()

    async def running(self) -> bool:
        compose_manager = await self.get_compose_manager()
        return await compose_manager.running()

    async def healthy(self) -> bool:
        compose_manager = await self.get_compose_manager()
        return await compose_manager.healthy("mc")

    async def wait_until_healthy(self) -> None:
        while not await self.healthy():
            await asyncio.sleep(0.5)

    async def get_server_info(self):
        """
        this method will return parsed compose file data
        """
        compose_obj = await self.get_compose_obj()

        assert (
            compose_obj.services is not None
        ), "Could not find services in compose file"
        compose_mc_service = compose_obj.services.get("mc")
        assert (
            compose_mc_service is not None
        ), "Could not find service mc in compose file"
        environment = compose_mc_service.environment
        assert type(environment) is dict, "Invalid environment in compose file"
        game_version = environment.get("VERSION")
        assert game_version is not None, "Could not find game version in compose file"
        assert type(game_version) is str

        ports = compose_mc_service.ports
        assert ports is not None, "Could not find ports in compose file"
        game_port = None
        rcon_port = None

        for port in ports:
            assert type(port) is Ports, "Something must be very wrong"
            if str(port.target) == "25565":
                game_port = port.published
                continue
            if str(port.target) == "25575":
                rcon_port = port.published
                continue

        assert game_port is not None, "Could not find game port in compose file"
        assert rcon_port is not None, "Could not find rcon port in compose file"

        return MCServerInfo(
            name=self._name,
            game_version=game_version,
            game_port=game_port,
            rcon_port=rcon_port,
        )

    async def list_players(self) -> list[str]:
        players = await self.send_command_rcon("list")
        if ":" not in players:
            return []
        players_str = players.split(":")[1].strip()
        return [
            player.strip() for player in players_str.split(",") if player.strip() != ""
        ]

    async def send_command_rcon(self, command: str) -> str:
        """
        this method will send a command to the server using rcon
            we are actually just using rcon-cli provided by itzg/minecraft-server
            to get rid of extra dependencies
        """
        compose_manager = await self.get_compose_manager()
        return await compose_manager.exec_command("mc", "rcon-cli", command)

    async def send_command_docker(self, command: str):
        """
        this method will send a command to the server using socat and docker attach
        """
        compose_manager = await self.get_compose_manager()
        await compose_manager.send_to_stdin("mc", command)
