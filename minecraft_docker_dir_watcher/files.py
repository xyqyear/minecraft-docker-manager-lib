import logging
import os
from typing import Optional, TypedDict

import aiofiles
from aiofiles import os as aioos
from ruamel.yaml import YAML

ServerInfoDictT = dict[str, int]


class DockerComposeFileT(TypedDict):
    version: str
    services: dict[str, dict[str, str | list[str]]]


yaml = YAML(typ="safe")


async def get_name_port_from_compose_file(path: str) -> Optional[ServerInfoDictT]:
    async with aiofiles.open(path, encoding="utf8") as f:
        compose_file_contents = await f.read()
    compose_file: DockerComposeFileT = yaml.load(compose_file_contents)

    if "services" not in compose_file:
        logging.warning(f"no services in {path}")
        return None

    services = compose_file["services"]

    for service_config in services.values():
        # server name
        if "container_name" not in service_config:
            logging.warning(f"no container_name in {path}")
            continue
        container_name = service_config["container_name"]
        if not isinstance(container_name, str):
            logging.warning(f"container_name is not a string in {path}")
            continue
        if not container_name.startswith("mc-"):
            continue
        server_name = container_name[3:]

        # port
        if "ports" not in service_config:
            continue
        mappings = service_config["ports"]
        if not isinstance(mappings, list):
            logging.warning(f"ports is not a list in {path}")
            continue

        ports = [
            m.split(":")[0]
            for m in mappings
            if m.endswith(":25565")  # type: ignore
        ]
        if not ports:
            continue
        port_str = ports[0]

        if not port_str.isdigit():
            continue

        return {server_name: int(port_str)}


async def get_server_info(path: str) -> ServerInfoDictT:
    sub_dir_paths: list[str] = []
    for f in await aioos.listdir(path):
        sub_dir_path = os.path.join(path, f)
        if await aioos.path.isdir(sub_dir_path):
            sub_dir_paths.append(sub_dir_path)

    server_info = ServerInfoDictT()
    for sub_dir_path in sub_dir_paths:
        # sub_dir_files = [f for f in await aioos.listdir(sub_dir_path)]
        sub_dir_files: list[str] = []
        try:
            for f in await aioos.listdir(sub_dir_path):
                sub_dir_files.append(f)
        except FileNotFoundError:
            continue

        compose_file: Optional[str] = None
        for sub_dir_file in sub_dir_files:
            if sub_dir_file in ["docker-compose.yaml", "docker-compose.yml"]:
                compose_file = sub_dir_file
                break

        if compose_file is None:
            continue

        compose_file_path = os.path.join(sub_dir_path, compose_file)

        try:
            single_server_info = await get_name_port_from_compose_file(
                compose_file_path
            )
        except FileNotFoundError:
            continue
        except PermissionError:
            logging.error(f"permission error on {compose_file_path}")
            continue
        except Exception as e:
            logging.error(f"unknown error on {compose_file_path}: {e}")
            continue

        if single_server_info is None:
            continue
        server_info.update(single_server_info)

    return server_info
