import asyncio
import shutil
from pathlib import Path


async def async_rmtree(path: Path):
    await asyncio.to_thread(shutil.rmtree, path)


async def run_shell_command(command: str, catch_output: bool = True) -> str:
    """
    need to use catch_stderr=False for socat
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE if catch_output else None,
        stderr=asyncio.subprocess.PIPE if catch_output else None,
    )

    stdout, stderr = await process.communicate()
    if stdout is None:  # type: ignore
        stdout = b""
    if stderr is None:  # type: ignore
        stderr = b""

    if process.returncode != 0:
        raise RuntimeError(f"Failed to run shell command: {command}\n{stderr.decode()}")
    return stdout.decode()


async def exec_command(command: str, *args: str) -> str:
    process = await asyncio.create_subprocess_exec(
        command,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    if stdout is None:  # type: ignore
        stdout = b""
    if stderr is None:  # type: ignore
        stderr = b""

    if process.returncode != 0:
        raise RuntimeError(f"Failed to exec command: {command}\n{stderr.decode()}")
    return stdout.decode()
