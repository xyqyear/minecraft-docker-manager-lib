# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
import pytest

from minecraft_docker_manager_lib.docker.compose_file import ComposeFile
from minecraft_docker_manager_lib.mc_compose_file import MCComposeFile


def test_mc_compose_file_basic():
    """测试MCComposeFile的基本功能"""
    test_data = {
        "services": {
            "mc": {
                "image": "itzg/minecraft-server:java21-alpine",
                "container_name": "mc-testserver",
                "environment": {
                    "EULA": "true",
                    "VERSION": "1.20.4",
                    "ENABLE_RCON": "true",
                },
                "ports": ["25565:25565", "25575:25575"],
                "volumes": ["./data:/data"],
                "stdin_open": True,
                "tty": True,
                "restart": "unless-stopped",
            }
        }
    }

    compose_obj = ComposeFile.from_dict(test_data)
    mc_compose = MCComposeFile(compose_obj)

    assert mc_compose.get_server_name() == "testserver"
    assert mc_compose.get_game_version() == "1.20.4"
    assert mc_compose.get_game_port() == 25565
    assert mc_compose.get_rcon_port() == 25575


def test_mc_compose_file_custom_ports():
    """测试自定义端口"""
    test_data = {
        "services": {
            "mc": {
                "image": "itzg/minecraft-server:java21-alpine",
                "container_name": "mc-customserver",
                "environment": {"VERSION": "1.19.4"},
                "ports": ["9999:25565", "9998:25575"],
                "stdin_open": True,
                "tty": True,
            }
        }
    }

    compose_obj = ComposeFile.from_dict(test_data)
    mc_compose = MCComposeFile(compose_obj)

    assert mc_compose.get_server_name() == "customserver"
    assert mc_compose.get_game_version() == "1.19.4"
    assert mc_compose.get_game_port() == 9999
    assert mc_compose.get_rcon_port() == 9998


def test_mc_compose_file_validation_errors():
    """测试验证错误"""
    # 没有services
    with pytest.raises(ValueError, match="Could not find services in compose file"):
        compose_obj = ComposeFile.from_dict({})
        MCComposeFile(compose_obj)

    # 没有mc服务
    with pytest.raises(ValueError, match="Could not find service mc in compose file"):
        compose_obj = ComposeFile.from_dict({"services": {"web": {}}})
        MCComposeFile(compose_obj)

    # 容器名不符合规范
    with pytest.raises(ValueError, match="Container name must start with 'mc-'"):
        test_data = {
            "services": {
                "mc": {
                    "container_name": "wrong-name",
                    "image": "itzg/minecraft-server",
                    "environment": {"VERSION": "1.20.4"},
                    "ports": ["25565:25565", "25575:25575"],
                }
            }
        }
        compose_obj = ComposeFile.from_dict(test_data)
        MCComposeFile(compose_obj)

    # 没有VERSION环境变量
    with pytest.raises(ValueError, match="Could not find VERSION in environment"):
        test_data = {
            "services": {
                "mc": {
                    "container_name": "mc-test",
                    "image": "itzg/minecraft-server",
                    "environment": {},
                    "ports": ["25565:25565", "25575:25575"],
                }
            }
        }
        compose_obj = ComposeFile.from_dict(test_data)
        MCComposeFile(compose_obj)


def test_mc_compose_file_get_server_name():
    """测试get_server_name方法"""
    test_data = {
        "services": {
            "mc": {
                "image": "itzg/minecraft-server:java21-alpine",
                "container_name": "mc-testserver",
                "environment": {"VERSION": "1.20.4"},
                "ports": ["25565:25565", "25575:25575"],
                "stdin_open": True,
                "tty": True,
            }
        }
    }

    compose_obj = ComposeFile.from_dict(test_data)
    mc_compose = MCComposeFile(compose_obj)

    assert mc_compose.get_server_name() == "testserver"
    
    # 测试不同的服务器名称
    test_data["services"]["mc"]["container_name"] = "mc-myserver123"
    compose_obj2 = ComposeFile.from_dict(test_data)
    mc_compose2 = MCComposeFile(compose_obj2)
    assert mc_compose2.get_server_name() == "myserver123"


def test_mc_compose_file_to_compose_file():
    """测试转换回ComposeFile"""
    test_data = {
        "services": {
            "mc": {
                "image": "itzg/minecraft-server:java21-alpine",
                "container_name": "mc-testserver",
                "environment": {"VERSION": "1.20.4"},
                "ports": ["25565:25565", "25575:25575"],
                "volumes": ["./data:/data"],
                "stdin_open": True,
                "tty": True,
                "restart": "unless-stopped",
            }
        }
    }

    compose_obj = ComposeFile.from_dict(test_data)
    mc_compose = MCComposeFile(compose_obj)

    # 转换回ComposeFile
    converted_compose = mc_compose.to_compose_file()

    # 验证可以再次创建MCComposeFile
    mc_compose2 = MCComposeFile(converted_compose)
    assert mc_compose2.get_server_name() == "testserver"
    assert mc_compose2.get_game_version() == "1.20.4"


if __name__ == "__main__":
    pytest.main()
