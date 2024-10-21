import pytest

from minecraft_docker_manager_lib.docker.compose_file import (
    ComposeFile,
    convert_str_port_to_obj,
    convert_str_volume_to_obj,
)
from minecraft_docker_manager_lib.docker.compose_models import Ports, Volumes


def test_convert_str_port_to_obj():
    # Test cases for convert_str_port_to_obj
    assert convert_str_port_to_obj("3000") == Ports(target="3000")
    assert convert_str_port_to_obj("3000-3005") == Ports(target="3000-3005")
    assert convert_str_port_to_obj("8000:8000") == Ports(
        published="8000", target="8000"
    )
    assert convert_str_port_to_obj("9090-9091:8080-8081") == Ports(
        published="9090-9091", target="8080-8081"
    )
    assert convert_str_port_to_obj("49100:22") == Ports(published="49100", target="22")
    assert convert_str_port_to_obj("8000-9000:80") == Ports(
        published="8000-9000", target="80"
    )
    assert convert_str_port_to_obj("127.0.0.1:8001:8001") == Ports(
        host_ip="127.0.0.1", published="8001", target="8001"
    )
    assert convert_str_port_to_obj("127.0.0.1:5000-5010:5000-5010") == Ports(
        host_ip="127.0.0.1", published="5000-5010", target="5000-5010"
    )
    assert convert_str_port_to_obj("6060:6060/udp") == Ports(
        published="6060", target="6060", protocol="udp"
    )


def test_convert_str_volume_to_obj():
    # Test cases for convert_str_volume_to_obj
    assert convert_str_volume_to_obj("/home:/home:ro") == Volumes(
        type="bind", source="/home", target="/home", read_only=True
    )
    assert convert_str_volume_to_obj(
        "/var/run/postgres/postgres.sock:/var/run/postgres/postgres.sock"
    ) == Volumes(
        type="bind",
        source="/var/run/postgres/postgres.sock",
        target="/var/run/postgres/postgres.sock",
    )
    assert convert_str_volume_to_obj("/data:/data") == Volumes(
        type="bind", source="/data", target="/data"
    )


def test_expand_services():
    # Test case for expand_services method in ComposeFile class
    compose_dict = {
        "services": {
            "web": {
                "ports": ["3000", "127.0.0.1:8001:8001", "6060:6060/udp"],
                "volumes": ["/home:/home:ro", "/data:/data"],
                "environment": ["KEY1=value1", "KEY2=value2"],
            }
        }
    }

    compose_file = ComposeFile.from_dict(compose_dict)

    assert compose_file.services["web"].ports == [
        Ports(target="3000"),
        Ports(host_ip="127.0.0.1", published="8001", target="8001"),
        Ports(published="6060", target="6060", protocol="udp"),
    ]

    assert compose_file.services["web"].volumes == [
        Volumes(type="bind", source="/home", target="/home", read_only=True),
        Volumes(type="bind", source="/data", target="/data"),
    ]

    assert compose_file.services["web"].environment == {
        "KEY1": "value1",
        "KEY2": "value2",
    }


def test_expand_services_with_dicts():
    # Test case for expand_services method when ports, environment, and volumes are already dicts
    compose_dict = {
        "services": {
            "web": {
                "ports": [
                    Ports(target="3000"),
                    Ports(host_ip="127.0.0.1", published="8001", target="8001"),
                    Ports(published="6060", target="6060", protocol="udp"),
                ],
                "volumes": [
                    Volumes(
                        type="bind", source="/home", target="/home", read_only=True
                    ),
                    Volumes(type="bind", source="/data", target="/data"),
                ],
                "environment": {"KEY1": "value1", "KEY2": "value2"},
            }
        }
    }

    compose_file = ComposeFile.from_dict(compose_dict)

    assert compose_file.services["web"].ports == [
        Ports(target="3000"),
        Ports(host_ip="127.0.0.1", published="8001", target="8001"),
        Ports(published="6060", target="6060", protocol="udp"),
    ]

    assert compose_file.services["web"].volumes == [
        Volumes(type="bind", source="/home", target="/home", read_only=True),
        Volumes(type="bind", source="/data", target="/data"),
    ]

    assert compose_file.services["web"].environment == {
        "KEY1": "value1",
        "KEY2": "value2",
    }


if __name__ == "__main__":
    pytest.main()
