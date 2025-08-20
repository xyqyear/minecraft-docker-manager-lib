#pyright: reportUnusedImport=false
import pytest

from minecraft_docker_manager_lib import DockerMCManager, MCComposeFile, MCServerInfo

from .test_integration import (
    TEST_ROOT_PATH,
    create_mc_server_compose_obj,
    teardown,
)


@pytest.mark.asyncio
async def test_minecraft_instance(teardown: list[str]):
    docker_mc_manager = DockerMCManager(TEST_ROOT_PATH)
    server1 = docker_mc_manager.get_instance("testserver1")
    teardown.append("mc-testserver1")

    await server1.create(create_mc_server_compose_obj("testserver1", 34544, 34544 + 1))
    assert await server1.get_server_info() == MCServerInfo(
        name="testserver1",
        game_version="1.20.4",
        game_port=34544,
        rcon_port=34545,
    )
    compose_obj = await server1.get_compose_obj()
    # 使用MCComposeFile进行强类型访问和修改
    mc_compose = MCComposeFile(compose_obj)
    
    # 修改游戏端口
    for port in mc_compose.mc_service["ports"]:
        if str(port.target) == "25565":
            port.published = "34546"
            break
    
    # 转换回ComposeFile进行保存
    updated_compose_obj = mc_compose.to_compose_file()
    await server1.update_compose_file(updated_compose_obj)
    assert await server1.get_server_info() == MCServerInfo(
        name="testserver1",
        game_version="1.20.4",
        game_port=34546,
        rcon_port=34545,
    )
