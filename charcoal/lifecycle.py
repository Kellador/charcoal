import asyncio
import logging
import os

from pathlib import Path

log = logging.getLogger(f'spiffy-mc.{__name__}')


async def serverStart(server: Path):
    """Start a given minecraft server.

    Parameters
    ----------
    server
        path to minecraft server,
        use 'find_server' or 'discover_servers'
        to get this
    """

    invocation = await get_invocation(server, split=True)

    os.chdir(server)  # TODO: add LOCK
    proc = await asyncio.create_subprocess_exec(
        'screen', '-h', '5000', '-dmS', server.name, *invocation, 'nogui'
    )
    await proc.wait()


async def serverStop(servername: str):
    """Stop a minecraft server.

    Parameters
    ----------
    servername
        name of the server
    """

    await sendCmds(
        servername,
        'title @a times 20 40 20',
        'title @a title {\"text\":\"STOPPING SERVER NOW\", \"bold\":true, \"italic\":true}',
        'broadcast Stopping now!',
        'save-all',
    )
    await asyncio.sleep(5)
    await sendCmd(servername, 'stop')


async def serverTerminate(server: str):
    """Terminates a serverprocess forcefully.

    Parameters
    ----------
    server
        name of the server, must be in the server's
        invocation in the form of <server>.jar

    Returns
    -------
        a boolean indicating whether the process,
        was successfully terminated
    """

    loop = asyncio.get_running_loop()
    _termProc = functools.partial(termProc, server)
    try:
        killed = await loop.run_in_executor(None, _termProc)
    except TerminationFailed:
        raise
    else:
        return killed


async def serverStatus(path: str | Path) -> dict:
    """Queries the status of all known Minecraft servers.

    Parameters
    ----------
    path
        parent directory of minecraft server directory

        'SpiffyPathNotFound' is raised if this directory
        does not exist!

    Returns
    -------
        a list of status messages for all queried servers
    """

    def _getStatus():
        servers = discover_servers(path)
        _status = {}
        for server in servers:
            _status[server.name] = True if isUp(server.name) else False
        return _status

    loop = asyncio.get_running_loop()
    try:
        status = await loop.run_in_executor(None, _getStatus)
    except SpiffyPathNotFound:
        raise
    else:
        return status