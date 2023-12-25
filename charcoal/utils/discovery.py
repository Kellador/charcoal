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


def get_backup(serverdir: Path) -> dict[str, List[Path]]:
    """Get all directories to backup for a given server.

    Parameters
    ----------
    serverdir
        directory of server to perform backup on

    Returns
    -------
        a dict of paths to include and exclude
    """

    world = serverdir / 'world'
    sb = serverdir / 'spiffy_backup'

    def _read_specification() -> dict[str, List[Path]]:
        with sb.open() as file:
            entries = file.read().split()

        specs = {'include': [], 'exclude': []}

        for e in entries:
            if e.startswith('-'):
                e_path = serverdir / e[1:]
                if e_path.exists():
                    specs['exclude'].append(e_path)
            else:
                if e.startswith('+'):  # Seems logical one might do this, so why not?!
                    e = e[1:]
                i_path = serverdir / e
                if i_path.exists():
                    specs['include'].append(i_path)

        return specs

    match world.exists(), sb.exists():
        case True, True:
            specification = _read_specification()
            if world not in specification['include']:
                specification['include'].append(world)
        case True, False:
            specification = {'include': [world], 'exclude': []}
        case False, True:
            specification = _read_specification()
        case False, False:
            raise NothingToBackup(serverdir)

    return specification


def get_procedures(serverdir: Path) -> dict[str, Any] | None:
    """Read special procedures file for a given server.

    Parameters
    ----------
    serverdir
        directory of server to get procedures for

    Returns
    -------
        a dict of procedures <format wip>
    """

    sp = serverdir / 'spiffy_procedures'

    if not sp.exists():
        return

    with sp.open() as file:
        procedures = json.load(file)

    return procedures


async def get_rcon_info(self, server: str) -> dict[str, str] | None:
        try:
            serverdir = find_server(self.parent_directory, server)
        except (SpiffyPathNotFound, SpiffyNameNotFound) as e:
            log.warning(e.message)
            raise e
        except SpiffyInvocationMissing as e:
            serverdir = e.path

        props = serverdir / 'server.properties'
        if props.exists():

            def _extract():
                with props.open() as _props:
                    lines = [
                        line.rstrip().split('=')
                        for line in _props
                        if line.startswith('rcon.') or line.startswith('enable-rcon')
                    ]
                if len(lines) != 3:
                    raise RconSettingsError(server)
                return {l[0]: l[1] for l in lines}

            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _extract)

            if enabled := info['enable-rcon']:
                if enabled == 'false':
                    raise RconNotEnabled(server)
            else:
                raise RconSettingsError(server)

            if info['rcon.port'] and info['rcon.password']:
                log.info(f'Extracted rcon information from {props}')
                return info
            else:
                raise RconLoginDetailsMissing(server)

        else:
            raise ServerPropertiesMissing(server)
        
        
def get_crashreport(server: Path, nthlast: int = 0) -> Path | None:
    """Retrieves the path of the nth latest crashreport for a given server.

    Parameters
    ----------
    server
        path to server
    nthlast, optional
        reports sorted newest to oldest, newest has index 0, by default 0

    Returns
    -------
        path of selected report

    Raises
    ------
    FileNotFoundError
        raised when crash-reports directory doesn't exist
    IndexError
        raised when nthlast does not exist
    """

    reports_dir = server / 'crash-reports'

    if not reports_dir.exists():
        raise FileNotFoundError

    reports = list(reports_dir.glob('*.txt'))

    if reports:
        reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        try:
            return reports[nthlast]
        except IndexError:
            raise IndexError
    else:
        return None