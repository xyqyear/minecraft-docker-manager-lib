import json
import subprocess
from pathlib import Path
from typing import Any

from asyncer import asyncify
from pydantic import BaseModel, Field

from ..utils import run_command


class DockerPsParsed(BaseModel):
    command: str = Field(alias="Command")
    created_at: str = Field(alias="CreatedAt")
    id: str = Field(alias="ID")
    image: str = Field(alias="Image")
    labels: dict[str, str] = Field(alias="Labels")
    local_volumes: str = Field(alias="LocalVolumes")
    mounts: str = Field(alias="Mounts")
    names: str = Field(alias="Names")
    networks: str = Field(alias="Networks")
    ports: str = Field(alias="Ports")
    running_for: str = Field(alias="RunningFor")
    size: str = Field(alias="Size")
    state: str = Field(alias="State")
    status: str = Field(alias="Status")

    @classmethod
    def parse_labels(cls, labels_str: str) -> dict[str, str]:
        return dict(label.split("=") for label in labels_str.split(","))

    @classmethod
    def from_docker_ps(cls, data: dict[str, Any]) -> "DockerPsParsed":
        data["Labels"] = cls.parse_labels(data["Labels"])
        return cls(**data)


class ComposeManager:
    def __init__(self, compose_file_path: str | Path) -> None:
        self.compose_file_path = Path(compose_file_path)

    async def run_command(self, command: str, *args: str) -> str:
        return await run_command(
            "docker", "compose", "-f", str(self.compose_file_path), command, *args
        )

    async def exec_command(self, service_name: str, command: str, *args: str) -> str:
        return await self.run_command("exec", service_name, command, *args)

    @asyncify
    def send_to_stdin(self, text: str):
        socat_command = [
            "socat",
            f"EXEC:docker compose -f {self.compose_file_path} attach mc,pty",
            "STDIN",
        ]
        echo_process = subprocess.Popen(["echo", text], stdout=subprocess.PIPE)
        socat_process = subprocess.Popen(socat_command, stdin=echo_process.stdout)
        _ = socat_process.communicate()

    async def up_detached(self):
        await self.run_command("up", "-d")

    async def down(self):
        await self.run_command("down")

    async def restart(self):
        await self.run_command("restart")

    async def pull(self):
        await self.run_command("pull")

    async def logs(self, tail: int = 1000) -> str:
        return await self.run_command("logs", "--tail", str(tail))

    async def running(self) -> bool:
        process = await self.run_command("ps", "-q")
        return process != ""

    async def created(self) -> bool:
        process = await self.run_command("ps", "--all", "-q")
        return process != ""


class DockerManager:
    async def run_command(self, command: str, *args: str) -> str:
        return await run_command("docker", command, *args, "--format", "json")

    async def ps(self):
        output = await self.run_command("ps", "--no-trunc")
        return [
            DockerPsParsed.from_docker_ps(json.loads(line))
            for line in output.splitlines()
        ]
