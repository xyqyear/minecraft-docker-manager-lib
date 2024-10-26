import asyncio
import random
from pathlib import Path

import aiofiles.os as aioos
import pytest
import pytest_asyncio

from minecraft_docker_manager_lib import (
    ComposeFile,
    DockerMCManager,
    MCPlayerMessage,
    MCServerInfo,
)
from minecraft_docker_manager_lib.utils import async_rmtree, run_command

from .mcc_docker_wrapper import MCCDockerWrapper

TEST_ROOT_PATH = Path("/tmp/test_temp_dir")


def create_mc_server_compose_obj(
    server_name: str, game_port: int, rcon_port: int
) -> ComposeFile:
    return ComposeFile.from_dict(
        {
            "services": {
                "mc": {
                    "image": "itzg/minecraft-server:java21-alpine",
                    "container_name": f"mc-{server_name}",
                    "environment": {
                        "EULA": "true",
                        "VERSION": "1.20.4",
                        "INIT_MEMORY": "0M",
                        "MAX_MEMORY": "500M",
                        "ONLINE_MODE": "false",
                        "TYPE": "VANILLA",
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
        await run_command(f"docker rm -f {container_name}")
    await async_rmtree(TEST_ROOT_PATH)


@pytest.mark.asyncio
async def test_integration(teardown: list[str]):
    # setting up
    docker_mc_manager = DockerMCManager(TEST_ROOT_PATH)

    server1 = docker_mc_manager.get_instance("testserver1")
    server2 = docker_mc_manager.get_instance("testserver2")
    client1 = MCCDockerWrapper(TEST_ROOT_PATH / "client1", "client1", "localhost:34544")
    client2 = MCCDockerWrapper(TEST_ROOT_PATH / "client2", "client2", "localhost:34544")
    teardown.append("mc-testserver1")
    teardown.append("mc-testserver2")
    teardown.append("mcc-client1")
    teardown.append("mcc-client2")

    assert not await server1.exists()
    assert not await server2.exists()

    assert set(await docker_mc_manager.get_all_server_names()) == set()

    server1_compose_obj = create_mc_server_compose_obj("testserver1", 34544, 34544 + 1)
    server2_compose_obj = create_mc_server_compose_obj("testserver2", 34554, 34554 + 1)
    server1_create_coroutine = server1.create(server1_compose_obj)
    server2_create_coroutine = server2.create(server2_compose_obj)
    await aioos.makedirs(TEST_ROOT_PATH / "irrelevant_dir", exist_ok=True)
    await asyncio.gather(server1_create_coroutine, server2_create_coroutine)
    assert set(await docker_mc_manager.get_all_server_names()) == set(
        ["testserver1", "testserver2"]
    )
    assert set(await docker_mc_manager.get_all_server_compose_paths()) == set(
        [
            TEST_ROOT_PATH / "testserver1/docker-compose.yml",
            TEST_ROOT_PATH / "testserver2/docker-compose.yml",
        ]
    )
    assert set(await docker_mc_manager.get_all_server_info()) == set(
        [
            MCServerInfo(
                name="testserver1",
                game_version="1.20.4",
                game_port=34544,
                rcon_port=34544 + 1,
            ),
            MCServerInfo(
                name="testserver2",
                game_version="1.20.4",
                game_port=34554,
                rcon_port=34554 + 1,
            ),
        ]
    )
    assert set(await docker_mc_manager.get_running_server_names()) == set()

    print("servers created")

    assert await server1.exists()
    assert not await server1.running()
    assert not await server1.healthy()
    assert not await server1.created()
    assert await server2.exists()
    assert not await server2.running()
    assert not await server2.healthy()
    assert not await server2.created()

    assert set(await docker_mc_manager.get_running_server_names()) == set()

    await server1.up()
    await server2.up()
    print("servers up")
    assert await server1.created()
    assert await server2.created()

    wait_server1_coroutine = server1.wait_until_healthy()
    wait_server2_coroutine = server2.wait_until_healthy()
    await asyncio.gather(wait_server1_coroutine, wait_server2_coroutine)

    assert await server1.running()
    assert await server1.healthy()
    assert await server2.running()
    assert await server2.healthy()
    assert set(await docker_mc_manager.get_running_server_names()) == set(
        ["testserver1", "testserver2"]
    )

    print("servers healthy")

    await server2.down()

    assert await server1.list_players() == []

    await client1.create()
    await client1.up()
    await client1.wait_until_connected()
    await asyncio.sleep(1)

    print("client1 connected")

    assert await server1.list_players() == ["client1"]

    await client2.create()
    await client2.up()
    await client2.wait_until_connected()
    await asyncio.sleep(1)

    print("client2 connected")

    assert set(await server1.list_players()) == set(["client1", "client2"])

    random_text1 = str(random.random())
    random_text2 = str(random.random())
    random_text3 = str(random.random())

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

    print("server1 verify chat 2")

    await client2.chat(random_text3)
    await asyncio.sleep(1)

    assert (await server1.get_player_messages_from_log())[0] == [
        MCPlayerMessage("client1", random_text1),
        MCPlayerMessage("client1", random_text2),
        MCPlayerMessage("client2", random_text3),
    ]

    print("server1 verify chat 3")

    await client1.down()
    await client2.down()

    assert await server1.list_players() == []

    await server1.stop()
    assert not await server1.running()
    assert not await server1.healthy()
    assert await server1.created()

    print("server1 stopped")

    await server1.start()
    assert await server1.running()

    await server1.wait_until_healthy()
    assert await server1.healthy()

    print("server1 started")

    await server1.restart()
    assert await server1.running()
    assert not await server1.healthy()

    await server1.wait_until_healthy()
    assert await server1.healthy()

    print("server1 restarted")

    await server1.down()
    assert not await server1.running()
    assert not await server1.healthy()
    assert not await server1.created()

    print("server1 down")
