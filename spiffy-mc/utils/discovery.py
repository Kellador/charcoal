import asyncio
import logging

log = logging.getLogger(f'spiffy-mc.{__name__}')


def discover_servers(path: str | Path) -> List[Path]:
    """Discover minecraft server locations.

    Discovery is dependent on the minecraft server having
    a 'spiffy_invocation' file in their directory.

    Parameters
    ----------
    path
        parent directory of minecraft server directories,
        only one level down from this parent is searched

        'SpiffyPathNotFound' is raised if this directory
        does not exist!

    Returns
    -------
        A list of paths to discovered minecraft servers
    """

    serverdir = Path(path)
    if not serverdir.exists():
        raise SpiffyPathNotFound(serverdir)

    servers = []

    for d in serverdir.iterdir():
        if d.is_dir():
            si = d / 'spiffy_invocation'
            if si.exists():
                servers.append(d)

    return servers


def find_server(path: str | Path, name: str) -> Path:
    """Find a minecraft server by it's given name and directory.

    Discovery is dependent on the minecraft server having
    a 'spiffy_invocation' file in their directory.

    Parameters
    ----------
    path
        parent directory of minecraft server directory

        'SpiffyPathNotFound' is raised if this directory
        does not exist!
    name
        name of server, must be identical to it's directory

    Returns
    -------
        the path to the server

        SpiffyNameNotFound is raised if no server by
        the given name is found

        SpiffyInvocationMissing is raised if server directory
        exists, but doesn't contain a 'spiffy_invocation'
    """

    serverdir = Path(path)
    if not serverdir.exists():
        raise SpiffyPathNotFound(serverdir)

    sdir = serverdir / name
    if sdir.exists():
        si = sdir / 'spiffy_invocation'
        if si.exists():
            return sdir
        else:
            raise SpiffyInvocationMissing(sdir)
    else:
        raise SpiffyNameNotFound(name)


async def get_invocation(serverdir: Path, split=False) -> str | List[str]:
    """Reads in the 'spiffy_invocation' file for a given server.

    Parameters
    ----------
    serverdir
        path to server,
        use 'find_server' to get this

    split, optional
        keep invocation as a list of components seperated
        by whitespace/newlines

    Returns
    -------
        the contents of 'spiffy_invocation' stripped of newlines
        and superfluous whitespace either as a single string
        or a list of components if split=True
    """

    si = serverdir / 'spiffy_invocation'

    def _extract():
        with si.open() as file:
            _invocation = file.read().split()

        if split:
            return _invocation
        else:
            return ' '.join(_invocation)

    loop = asyncio.get_running_loop()
    invocation = await loop.run_in_executor(None, _extract)
    return invocation

