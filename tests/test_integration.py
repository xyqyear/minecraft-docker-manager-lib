import asyncio
import random
from pathlib import Path

import aiofiles.os as aioos
import pytest
import pytest_asyncio

from minecraft_docker_manager_lib.docker.compose_file import ComposeFile
from minecraft_docker_manager_lib.instance import MCPlayerMessage
from minecraft_docker_manager_lib.manager import DockerMCManager
from minecraft_docker_manager_lib.utils import async_rmtree, run_command

from .mcc_docker_wrapper import MCCDockerWrapper

TEST_ROOT_PATH = Path("/tmp/test_temp_dir")


def create_mc_server_compose_obj(
    image_version: str, server_name: str, game_port: int, rcon_port: int
) -> ComposeFile:
    return ComposeFile.from_dict(
        {
            "services": {
                "mc": {
                    "image": f"itzg/minecraft-server:{image_version}",
                    "container_name": f"mc-{server_name}",
                    "environment": {
                        "EULA": "true",
                        "VERSION": "1.20.4",
                        "INIT_MEMORY": "0M",
                        "MAX_MEMORY": "500M",
                        "ONLINE_MODE": "false",
                        "TYPE": "PAPER",
                        "ENABLE_RCON": "true",
                        "MODE": "creative",
                        "VIEW_DISTANCE": "1",
                        "LEVEL_TYPE": "minecraft:flat",
                        "GENERATE_STRUCTURES": "false",
                        "SPAWN_NPCS": "false",
                        "SPAWN_ANIMALS": "false",
                        "SPAWN_MONSTERS": "false",
                        "FORCE_GAMEMODE": "true",
                    },
                    "ports": [f"{game_port}:25565", f"{rcon_port}:25575"],
                    "volumes": ["./data:/data"],
                    "stdin_open": True,
                    "tty": True,
                    "restart": "unless-stopped",
                }
            }
        }
    )


@pytest_asyncio.fixture  # type: ignore
async def teardown():
    if await aioos.path.exists(TEST_ROOT_PATH):
        await async_rmtree(TEST_ROOT_PATH)
    await aioos.makedirs(TEST_ROOT_PATH)
    containers_to_remove = list[str]()
    yield containers_to_remove
    for container_name in containers_to_remove:
        await run_command("docker", "rm", "-f", container_name)
    await async_rmtree(TEST_ROOT_PATH)


@pytest.mark.asyncio
async def test_instance(teardown: list[str]):
    docker_mc_manager = DockerMCManager(TEST_ROOT_PATH)
    server1_port = 34544

    server1 = docker_mc_manager.get_instance("testserver1")
    client1 = MCCDockerWrapper(
        TEST_ROOT_PATH / "client1", "client1", f"localhost:{server1_port}"
    )
    teardown.append("mc-testserver1")
    teardown.append("mcc-client1")

    await server1.create(
        create_mc_server_compose_obj(
            "java21-alpine", "testserver1", server1_port, server1_port + 1
        )
    )

    print("server1 created")

    assert not await server1.running()
    assert not await server1.healthy()

    await server1.up()
    print("server1 up")
    await server1.wait_until_healthy()

    print("server1 healthy")

    assert await server1.running()
    assert await server1.healthy()

    print("server1 really healthy")

    assert await server1.list_players() == []

    await client1.create()
    await client1.up()
    await client1.wait_until_connected()
    await asyncio.sleep(1)

    print("client1 connected")

    assert await server1.list_players() == ["client1"]

    random_text1 = str(random.random())
    random_text2 = str(random.random())

    await client1.chat(random_text1)
    await asyncio.sleep(1)

    print("client1 chat")

    messages, pointer = await server1.get_player_messages_from_log()
    assert messages == [MCPlayerMessage("client1", random_text1)]

    print("server1 verify chat")

    await client1.chat(random_text2)
    await asyncio.sleep(1)

    assert (await server1.get_player_messages_from_log())[0] == [
        MCPlayerMessage("client1", random_text1),
        MCPlayerMessage("client1", random_text2),
    ]

    assert (await server1.get_player_messages_from_log(pointer))[0] == [
        MCPlayerMessage("client1", random_text2),
    ]

    print("server1 verify 2 chat")

    await client1.down()

    assert await server1.list_players() == []

    await server1.stop()
    assert not await server1.running()
    assert not await server1.healthy()
    assert await server1.created()

    await server1.start()
    assert await server1.running()

    await server1.restart()
    assert await server1.running()
    assert not await server1.healthy()

    await server1.down()
    assert not await server1.running()
    assert not await server1.healthy()
    assert not await server1.created()
