import asyncio
import logging

import psutil

from .exceptions import TerminationFailed

log = logging.getLogger(f'spiffy-mc.{__name__}')


def isUp(server: str) -> bool:
    """Checks whether a server is up, by searching for its process.

    Parameters
    ----------
    server
        name of server, must be in server's invocation
        in the form of '<server>.jar' somewhere

    Returns
    -------
        a boolean indicating whether the server is up or not
    """

    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']:  # type: ignore
            return True
    return False


def getProc(server: str) -> psutil.Process | None:
    """Finds and returns the Process object for a given server.

    Parameters
    ----------
    server
        name of server, must be in server's invocation
        in the form of '<server>.jar' somewhere

    Returns
    -------
        server process (psutil.Process) or None if not found
    """

    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']: # type: ignore
            return process
    return None


def termProc(server: str) -> bool:
    """Finds the process for a given server and terminates it.

    Parameters
    ----------
    server
        name of server, must be in server's invocation
        in the form of '<server>.jar' somewhere

    Returns
    -------
        True if process was found and successfully terminated
        False if process was not found

        Raises TerminationFailed if process was found, but
        resisted termination
    """

    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']: # type: ignore
            toKill = process.children()
            toKill.append(process)
            for p in toKill:
                p.terminate()
            _, alive = psutil.wait_procs(toKill, timeout=3)
            for p in alive:
                p.kill()
            _, alive = psutil.wait_procs(toKill, timeout=3)
            if not alive:
                return True
            else:
                raise TerminationFailed(server)
    return False