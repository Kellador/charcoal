import asyncio
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .exceptions import (
    NoProcedures,
    NoReportDirectory,
    NoReports,
    ParentDirMissing,
    NoInvocation,
    RconNotEnabled,
    ServerNotFound,
    NothingToBackup,
    ServerPropertiesMissing,
    RconLoginDetailsMissing,
    RconSettingsError,
)


class CharcoalStatus(Enum):
    UNTRACKED = -1
    DISABLED = 0
    ENABLED = 1


def discover_servers(path: str | Path) -> Dict[str, List[Path]]:
    """Search a directory for immediate subdirectories containing a server tracked by charcoal,
    as indicated by the presence of a 'charcoal_enabled' or 'charcoal_disabled' file.

    If both files are present, 'charcoal_enabled' takes presedence!

    Parameters
    ----------
    path
        path of directory to search for immediate subdirectories in

    Returns
    -------
        mapping of 'enabled' and 'disabled' servers, identified by their base path

    Raises
    ------
    ParentDirMissing
        raised when given path does not exist
    """

    serverdir = Path(path)
    if not serverdir.exists():
        raise ParentDirMissing(serverdir)

    servers = {'enabled': [], 'disabled': []}

    for d in serverdir.iterdir():
        if d.is_dir():
            se = d / 'charcoal_enabled'
            if se.exists():
                servers['enabled'].append(se)
                continue
            sd = d / 'charcoal_disabled'
            if sd.exists():
                servers['disabled'].append(sd)
                continue

    return servers


def find_server(path: str | Path, name: str) -> Tuple[Path, CharcoalStatus]:
    """Search for a specific server, by searching in the given directory for immediate subdirectories matching the given name.

    Parameters
    ----------
    path
        path of directory to search for immediate subdirectories in
    name
        name of server to search for, it's base directory must match this name

    Returns
    -------
        a tuple of the found server's path and it's status regarding charcoal integration

    Raises
    ------
    ParentDirMissing
        raised if given directory does not exist
    ServerNotFound
        raised if no server matching the given name can be found
    """

    serverdir = Path(path)
    if not serverdir.exists():
        raise ParentDirMissing(serverdir)

    sdir = serverdir / name
    if sdir.exists():
        se = sdir / 'charcoal_enabled'
        if se.exists():
            return (sdir, CharcoalStatus.ENABLED)
        sd = sdir / 'charcoal_disabled'
        if sd.exists():
            return (sdir, CharcoalStatus.DISABLED)
        return (sdir, CharcoalStatus.UNTRACKED)
    else:
        raise ServerNotFound(sdir)


async def get_invocation(serverdir: Path) -> str | List[str]:
    """Look for, and parse, the 'charcoal_invocation' file for a given server directory.

    Parameters
    ----------
    serverdir
        path to server base directory

    Returns
    -------
        extracted server start invocation/command

    Raises
    ------
    NoInvocation
        raised if 'charcoal_invocation' file does not exist
    """

    si = serverdir / 'charcoal_invocation'

    if not si.exists():
        raise NoInvocation(serverdir)

    def _extract():
        with si.open() as file:
            _invocation = file.read().split()
            return ' '.join(_invocation)

    loop = asyncio.get_running_loop()
    invocation = await loop.run_in_executor(None, _extract)
    return invocation


def get_backup_spec(
    serverdir: Path, always_include_world: bool = True
) -> dict[str, List[Path]]:
    """Search for, and parse, the 'charcoal_backup' file for a given server directory.

    Parameters
    ----------
    serverdir
        path to server base directory
    always_include_world, optional
        whether or not to explicitly include the 'world' directory, by default True

    Returns
    -------
        mapping of explicitly included and excluded paths

    Raises
    ------
    NothingToBackup
        raised if 'world' isn't explicitly included | does not exist, and 'charcoal_backup' file does not exist
    """

    world = serverdir / 'world'
    sb = serverdir / 'charcoal_backup'

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

    match (world.exists() and always_include_world), sb.exists():
        case True, True:
            specification = _read_specification()
            if world not in specification['include']:
                specification['include'].append(world)
            return specification
        case True, False:
            specification = {'include': [world], 'exclude': []}
            return specification
        case False, True:
            specification = _read_specification()
            return specification
        case _, _:
            raise NothingToBackup(serverdir)


def get_procedures(serverdir: Path) -> dict[str, Any]:  # TODO - Procedure Type
    """Search for, and parse, the 'charcoal_procedures' file for a given server directory.

    Parameters
    ----------
    serverdir
        path to server base directory

    Returns
    -------
        procedures # TODO

    Raises
    ------
    NoProcedures
        raised if 'charcoal_procedures' file does not exist
    """

    sp = serverdir / 'charcoal_procedures'

    if not sp.exists():
        raise NoProcedures(serverdir)

    with sp.open() as file:
        procedures = json.load(file)

    return procedures


async def get_rcon_spec(serverdir: Path) -> dict[str, str]:  # TODO - RCON Type
    """Search for, and parse, the 'server.properties' file for a given server directory.

    Parameters
    ----------
    serverdir
        path to server base directory

    Returns
    -------
        rcon info # TODO

    Raises
    ------
    ServerPropertiesMissing
        raised if 'server.properties' file does not exist
    RconSettingsError
        raised if 'server.properties' does not contain all necessary rcon entries
    RconNotEnabled
        raised if 'enable-rcon' is set to 'false' in 'server.properties'
    RconLoginDetailsMissing
        raised if rcon port and/or password are not set in 'server.properties'
    """

    props = serverdir / 'server.properties'

    if not props.exists():
        raise ServerPropertiesMissing(serverdir)

    def _extract():
        with props.open() as _props:
            lines = [
                line.rstrip().split('=')
                for line in _props
                if line.startswith('rcon.') or line.startswith('enable-rcon')
            ]
        if len(lines) != 3:
            raise RconSettingsError(serverdir)
        return {l[0]: l[1] for l in lines}

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _extract)

    if enabled := info['enable-rcon']:
        if enabled == 'false':
            raise RconNotEnabled(serverdir)
    else:
        raise RconSettingsError(serverdir)

    if info['rcon.port'] and info['rcon.password']:
        return info
    else:
        raise RconLoginDetailsMissing(serverdir)


def get_crashreport(serverdir: Path, nthlast: int = 0) -> Path:
    """Search for latest, or other, crash report in given server directory.

    Parameters
    ----------
    serverdir
        path to server base directory
    nthlast, optional
        n-th last report to look for, by default 0 (latest)

    Returns
    -------
        path to crash report

    Raises
    ------
    NoReportDirectory
        raised if 'crash-reports' directory does not exist
    NoReports
        raised if no crash reports exist
    """

    reports_dir = serverdir / 'crash-reports'

    if not reports_dir.exists():
        raise NoReportDirectory(serverdir)

    reports = list(reports_dir.glob('*.txt'))

    if reports:
        reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        if (nthlast + 1) > len(reports):
            nthlast = len(reports) - 1

        return reports[nthlast]
    else:
        raise NoReports(serverdir)
