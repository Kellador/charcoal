import asyncio
import logging

log = logging.getLogger(f'spiffy-mc.{__name__}')


async def sendCmds(server: str, *cmds: str):
    """Passes all given command strings to a server's screen.

    Parameters
    ----------
    server
        name of server's screen instance

    cmds, variadic
        commands to be executed
    """

    for cmd in cmds:
        log.info(f'Sending \"{cmd}\" to {server}.')
        proc = await asyncio.create_subprocess_exec(
            'screen', '-S', server, '-X', 'stuff', f'{cmd}\r'
        )
        await proc.wait()