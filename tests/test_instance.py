#pyright: reportUnusedImport=false
import pytest

from minecraft_docker_manager_lib import DockerMCManager, MCComposeFile, MCServerInfo

from .test_utils import (
    TEST_ROOT_PATH,
    create_mc_server_compose_yaml,
    teardown,
)


@pytest.mark.asyncio
async def test_minecraft_instance(teardown: list[str]):
    docker_mc_manager = DockerMCManager(TEST_ROOT_PATH)
    server1 = docker_mc_manager.get_instance("testserver1")
    teardown.append("mc-testserver1")

    await server1.create(create_mc_server_compose_yaml("testserver1", 34544, 34544 + 1))
    assert await server1.get_server_info() == MCServerInfo(
        name="testserver1",
        game_version="1.20.4",
        game_port=34544,
        rcon_port=34545,
    )
    compose_obj = await server1.get_compose_obj()
    mc_compose = MCComposeFile(compose_obj)

    assert mc_compose.get_server_name() == "testserver1"
    assert mc_compose.get_game_version() == "1.20.4"
    assert mc_compose.get_game_port() == 34544
    assert mc_compose.get_rcon_port() == 34545
