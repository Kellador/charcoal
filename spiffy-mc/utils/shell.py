import asyncio
import logging

log = logging.getLogger(f'spiffy-mc.{__name__}')


async def exec_shell_cmd(*args: str) -> str:
    """Runs a given shell command and returns the output"""

    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    log.info('Executing:', args)
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        log.info('Finished:', args)
    else:
        log.info('Failed:', args)
    return stdout.decode().strip()
