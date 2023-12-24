import asyncio
import logging

from pathlib import Path

log = logging.getLogger(f'spiffy-mc.{__name__}')


def getcrashreport(server: Path, nthlast: int = 0) -> Path | None:
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