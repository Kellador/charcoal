import asyncio
import logging

import psutil

from .exceptions import ProcessNotFound, TerminationFailed

log = logging.getLogger(f'spiffy-mc.{__name__}')

# If you're wondering what all the 'type: ignore' comments are about:
# process.info is an attribute of psutil's Process objects, that
# only exists if created through psutil.process_iter;
# type-checking does not recognize this, thus we ignore it.


class ServerProcess:
    def __init__(self, name: str) -> None:
        self.name = name

    def _post_init(self):
        for process in psutil.process_iter(
            attrs=[
                'cmdline',
                'create_time',
                'name',
                'username',
                'num_threads',
                'memory_percent',
            ]
        ):
            if name in process.info['cmdline']:  # type: ignore
                if len(process.children()) > 0:
                    self.process = process
                    self.cmdline = process.info['cmdline']  # type: ignore
                    self.create_time = process.info['create_time']  # type: ignore
                    self.process_name = process.info['name']  # type: ignore
                    self.username = process.info['username']  # type: ignore
                    self.num_threads = process.info['num_threads']  # type: ignore
                    self.memory_percent = process.info['memory_percent']  # type: ignore
        else:
            raise ProcessNotFound(self.name)

    @classmethod
    async def find(cls, name: str):
        """Look for a server's process and wrap it in a ServerProcess,
        capable of interacting with the server process

        Parameters
        ----------
        name
            name of the server, this should be a unique identifier;
            it must be present in the commandline used to start the server process

        Returns
        -------
            a ServerProcess

        Raises
        ------
        ProcessNotFound
            raised if no process can be found with the given name in it's commandline
        """

        self = cls(name)
        try:
            await asyncio.get_running_loop().run_in_executor(None, self._post_init)
        except:
            raise
        return self

    async def is_running(self) -> bool:
        """Check if process is present in current process list.

        Returns
        -------
            whether process is running or not
        """

        running = await asyncio.get_running_loop().run_in_executor(
            None, self.process.is_running
        )
        return running

    def _terminate(self, timeout: int = 3):
        processes = self.process.children(recursive=True)
        processes.append(self.process)
        for p in processes:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(processes, timeout=timeout)
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(processes, timeout=timeout)
        if alive:
            raise TerminationFailed(self.name)

    async def terminate(self, timeout: int = 3):
        """Terminate server process, and all its children.

        Parameters
        ----------
        timeout, optional
            time in seconds to wait for termination,
            once for sig term, and again for sig kill,
            if sig term failed, by default 3

        Raises
        ------
        TerminationFailed
            raised if process or process children remain after sig term and sig kill
        """

        try:
            await asyncio.get_running_loop().run_in_executor(
                None, self._terminate, timeout
            )
        except:
            raise


def checkServerRunning(name: str) -> bool:
    """Check if server process is present in current process list.

    Use this if you only need to check if a server process exists once or twice;
    for all other purposes it'll be more efficient to grab a `ServerProcess`

    Parameters
    ----------
    servername
        name of the server, this should be a unique identifier;
        it must be present in the commandline used to start the server process

    Returns
    -------
        whether a process for given server name was found or not
    """

    for process in psutil.process_iter(attrs=['cmdline']):
        if name in process.info['cmdline']:  # type: ignore
            return True
    return False
