import asyncio
import json
from pathlib import Path
from typing import Any

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


class Publisher(BaseModel):
    URL: str
    TargetPort: int
    PublishedPort: int
    Protocol: str


class DockerComposePsParsed(DockerPsParsed):
    exit_code: int = Field(alias="ExitCode")
    health: str = Field(alias="Health")
    name: str = Field(alias="Name")
    project: str = Field(alias="Project")
    publishers: list[Publisher] = Field(alias="Publishers")
    service: str = Field(alias="Service")

    @classmethod
    def from_docker_compose_ps(cls, data: dict[str, Any]) -> "DockerComposePsParsed":
        data["Labels"] = cls.parse_labels(data["Labels"])
        return cls(**data)


class ComposeManager:
    def __init__(self, project_path: str | Path) -> None:
        self.project_path = Path(project_path)

    async def run_command(self, command: str) -> str:
        return await run_command(
            f"docker compose --project-directory {self.project_path} {command}"
        )

    async def exec_command(self, service_name: str, command: str) -> str:
        return await self.run_command(f"exec {service_name} {command}")

    async def send_to_stdin(self, service_name: str, text: str):
        socat_process = await asyncio.create_subprocess_shell(
            f'echo "{text}" | socat "EXEC:docker compose --project-directory {self.project_path} attach {service_name},pty" STDIN',
        )
        await socat_process.wait()

    async def up_detached(self):
        await self.run_command("up -d")

    async def down(self):
        await self.run_command("down")

    async def restart(self):
        await self.run_command("restart")

    async def pull(self):
        await self.run_command("pull")

    async def logs(self, tail: int = 1000) -> str:
        return await self.run_command(f"logs --tail {tail}")

    async def running(self) -> bool:
        process = await self.run_command("ps -q")
        return process != ""

    async def created(self) -> bool:
        process = await self.run_command("ps --all -q")
        return process != ""

    async def ps(self, service_name: str) -> DockerComposePsParsed:
        output = await self.run_command("ps --no-trunc --format json")
        for line in output.splitlines():
            parsed = DockerComposePsParsed.from_docker_compose_ps(json.loads(line))
            if parsed.service == service_name:
                return parsed
        raise ValueError(f"Could not find service {service_name}")

    async def healthy(self, service_name: str) -> bool:
        try:
            compose_ps = await self.ps(service_name)
        except ValueError:
            return False
        return compose_ps.health == "healthy"


class DockerManager:
    async def run_command(self, sub_command: str) -> str:
        # return await run_command("docker", command, *args, "--format", "json")
        return await run_command(f"docker {sub_command} --format json")

    async def ps(self):
        output = await self.run_command("ps --no-trunc")
        return [
            DockerPsParsed.from_docker_ps(json.loads(line))
            for line in output.splitlines()
        ]
