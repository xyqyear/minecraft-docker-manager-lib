import shutil
import subprocess
from pathlib import Path

from asyncer import asyncify


@asyncify
def async_rmtree(path: str | Path):
    shutil.rmtree(path)


@asyncify
def run_command(*commands: str) -> str:
    process = subprocess.run(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.stdout
