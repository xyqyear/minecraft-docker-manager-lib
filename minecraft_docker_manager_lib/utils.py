import asyncio
import shutil
from pathlib import Path


async def async_rmtree(path: Path):
    await asyncio.to_thread(shutil.rmtree, path)


async def run_command(command: str) -> str:
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Failed to run command: {command}\n{stderr.decode()}")
    return stdout.decode()
