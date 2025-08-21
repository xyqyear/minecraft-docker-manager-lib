import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aiofiles.os as aioos
import yaml

from .docker.compose_file import ComposeFile
from .docker.manager import ComposeManager
from .mc_compose_file import MCComposeFile
from .utils import async_rmtree

PLAYER_MESSAGE_PATTERN = re.compile(
    r"\]: (?:\[Not Secure\] )?<(?P<player>.*?)> (?P<message>.*)"
)
ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@dataclass
class LogType:
    content: str
    pointer: int


@dataclass(frozen=True)
class MCServerInfo:
    name: str
    game_version: str
    game_port: int
    rcon_port: int


@dataclass
class MCPlayerMessage:
    player: str
    message: str


class MCInstance:
    def __init__(self, servers_path: str | Path, name: str) -> None:
        self._servers_path = Path(servers_path)
        self._name = name
        self._project_path = self._servers_path / self._name
        self._compose_manager = ComposeManager(self._project_path)

    def get_name(self) -> str:
        return self._name

    def get_project_path(self) -> Path:
        return self._project_path

    def get_compose_manager(self) -> ComposeManager:
        return self._compose_manager

    async def get_compose_file_path(self) -> Path | None:
        candidates = [
            self._project_path / "docker-compose.yml",
            self._project_path / "docker-compose.yaml",
            self._project_path / "compose.yml",
            self._project_path / "compose.yaml"
        ]
        
        existence_checks = await asyncio.gather(
            *[aioos.path.exists(path) for path in candidates],
            return_exceptions=True
        )
        
        for path, exists in zip(candidates, existence_checks):
            if exists is True:
                return path
        
        return None

    def verify_compose_obj(self, compose_obj: ComposeFile) -> bool:
        """
        验证compose文件是否符合Minecraft服务器要求
        
        MCComposeFile初始化会验证所有基本要求，
        成功后只需检查服务器名称是否匹配。
        """
        try:
            # MCComposeFile初始化成功 = 格式验证通过
            mc_compose = MCComposeFile(compose_obj)
        except ValueError:
            return False
        return mc_compose.get_server_name() == self._name

    def verify_compose_yaml(self, compose_yaml: str) -> bool:
        """
        验证YAML字符串是否符合Minecraft服务器要求
        
        将YAML字符串转换为ComposeFile对象并验证。
        """
        try:
            compose_dict = yaml.load(compose_yaml, Loader=yaml.CLoader)
            compose_obj = ComposeFile.from_dict(compose_dict)
            return self.verify_compose_obj(compose_obj)
        except (yaml.YAMLError, ValueError, Exception):
            return False

    async def get_compose_file(self) -> str:
        """
        Get the current compose file content as a YAML string
        
        Returns:
            str: The current compose.yaml file content
            
        Raises:
            FileNotFoundError: If compose.yaml doesn't exist for this server
        """
        compose_file_path = await self.get_compose_file_path()
        if compose_file_path is None:
            raise FileNotFoundError(
                f"Could not find compose.yaml for server {self._name}"
            )
        
        async with aiofiles.open(compose_file_path, "r", encoding="utf8") as file:
            return await file.read()

    async def get_compose_obj(self) -> ComposeFile:
        compose_file_path = await self.get_compose_file_path()
        if compose_file_path is None:
            raise FileNotFoundError(
                f"Could not find compose.yaml for server {self._name}"
            )
        compose_obj = await ComposeFile.async_from_file(compose_file_path)

        if self.verify_compose_obj(compose_obj):
            return compose_obj

        raise FileNotFoundError(
            f"Could not find valid compose.yaml file for server {self._name}"
        )

    def _get_log_path(self) -> Path:
        return self._project_path / "data" / "logs" / "latest.log"

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

    @staticmethod
    def parse_player_messages_from_log(log: str) -> list[MCPlayerMessage]:
        return [
            MCPlayerMessage(
                player=match.group("player"), message=match.group("message")
            )
            for match in PLAYER_MESSAGE_PATTERN.finditer(log)
        ]

    async def get_player_messages_from_log(
        self, start: int = 0
    ) -> tuple[list[MCPlayerMessage], int]:
        log = await self.get_logs_from_file(start)
        return self.parse_player_messages_from_log(log.content), log.pointer

    async def get_logs_from_docker(self, tail: int = 1000) -> str:
        return await self._compose_manager.logs(tail)

    async def create(self, compose_yaml: str) -> None:
        """
        create a new directory for the server and write the compose file to it
        it also creates a data directory for the server
        
        Args:
            compose_yaml: Docker compose configuration as YAML string
            
        Raises:
            ValueError: If YAML is invalid or doesn't meet Minecraft server requirements
            FileExistsError: If compose.yaml already exists for this server
        """
        if not self.verify_compose_yaml(compose_yaml):
            raise ValueError("Invalid compose YAML or doesn't meet Minecraft server requirements")

        await aioos.makedirs(self._project_path, exist_ok=True)
        if await self.get_compose_file_path() is not None:
            raise FileExistsError(
                f"compose.yaml already exists for server {self._name}"
            )
        
        compose_file_path = self._project_path / "compose.yaml"
        async with aiofiles.open(compose_file_path, "w", encoding="utf8") as file:
            await file.write(compose_yaml)
        
        await aioos.makedirs(self._project_path / "data", exist_ok=True)

    async def update_compose_file(self, compose_yaml: str) -> None:
        """
        Update the compose file for the server with a new YAML configuration
        
        Args:
            compose_yaml: Docker compose configuration as YAML string
            
        Raises:
            RuntimeError: If server is currently created/running
            ValueError: If YAML is invalid or doesn't meet Minecraft server requirements
            FileNotFoundError: If compose.yaml doesn't exist for this server
        """
        if await self.created():
            raise RuntimeError(f"Cannot update server {self._name} while it is created")
        if not self.verify_compose_yaml(compose_yaml):
            raise ValueError("Invalid compose YAML or doesn't meet Minecraft server requirements")

        compose_file_path = await self.get_compose_file_path()
        if compose_file_path is None:
            raise FileNotFoundError(
                f"Could not find compose.yaml for server {self._name}"
            )
        
        # Write YAML string directly to file
        async with aiofiles.open(compose_file_path, "w", encoding="utf8") as file:
            await file.write(compose_yaml)

    async def remove(self) -> None:
        if await self._compose_manager.created():
            raise RuntimeError(f"Cannot remove server {self._name} while it is created")
        await async_rmtree(self._project_path)

    async def up(self) -> None:
        await self._compose_manager.up_detached()

    async def down(self) -> None:
        await self._compose_manager.down()

    async def start(self) -> None:
        await self._compose_manager.start()

    async def stop(self) -> None:
        await self._compose_manager.stop()

    async def restart(self) -> None:
        await self._compose_manager.restart()

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
        return await self._compose_manager.created()

    async def running(self) -> bool:
        return await self._compose_manager.running()

    async def healthy(self) -> bool:
        return await self._compose_manager.healthy("mc")

    async def paused(self) -> bool:
        mc_health_result = await self._compose_manager.exec("mc", "mc-health")
        if "Java process suspended by Autopause function" in mc_health_result:
            return True
        return False

    async def wait_until_healthy(self) -> None:
        if not await self.running():
            raise RuntimeError(f"Server {self._name} is not running")
        while not await self.healthy():
            await asyncio.sleep(0.5)

    async def get_server_info(self):
        """
        获取服务器信息
        
        使用MCComposeFile进行强类型访问，一旦MCComposeFile创建成功，
        就意味着所有必需的字段都已经验证并且类型正确。
        """
        compose_obj = await self.get_compose_obj()
        mc_compose = MCComposeFile(compose_obj)  # 完成所有验证和类型转换
        
        # 此时可以安全地调用强类型方法，无需额外的类型检查
        return MCServerInfo(
            name=mc_compose.get_server_name(),
            game_version=mc_compose.get_game_version(),
            game_port=mc_compose.get_game_port(),
            rcon_port=mc_compose.get_rcon_port(),
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
        if not await self.healthy():
            raise RuntimeError(f"Server {self._name} is not healthy")
        result = await self._compose_manager.exec("mc", "rcon-cli", command)
        return ANSI_ESCAPE_PATTERN.sub("", result).strip()

    async def send_command_stdin(self, command: str):
        """
        this method will send a command to the server using mc-send-to-console
        """
        if not await self.healthy():
            raise RuntimeError(f"Server {self._name} is not healthy")
        await self._compose_manager.exec("mc", "mc-send-to-console", command)
