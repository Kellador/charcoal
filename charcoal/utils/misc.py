import asyncio
import logging
import re

log = logging.getLogger(f'spiffy-mc.{__name__}')


def buildCountdownSteps(cntd):
    """Builds and returns a list of countdown step triples,
    consisting of 'time to announce', 'time in seconds to wait',
    and 'the timeunit to announce'.
    """

    countpat = re.compile(
        r'(?P<time>\d+)((?P<minutes>[m].*)|(?P<seconds>[s].*))', flags=re.I
    )
    steps = []
    for i, step in enumerate(cntd):
        s = countpat.search(step)
        if s is None:
            raise  # TODO
        if s.group('minutes'):
            time = int(s.group('time'))
            secs = time * 60
            unit = 'minutes'
        else:
            time = int(s.group('time'))
            secs = time
            unit = 'seconds'
        if i + 1 > len(cntd) - 1:
            steps.append((time, secs, unit))
        else:
            st = countpat.search(cntd[i + 1])
            if st is None:
                raise  # TODO
            if st.group('minutes'):
                t = int(st.group('time')) * 60
            else:
                t = int(st.group('time'))
            steps.append((time, secs - t, unit))
    return steps


def formatStatus(statusmap: dict) -> str:
    """Pretty print server status, basically.

    Parameters
    ----------
    statusmap
        server status dict,
        as produced by 'serverStatus'

    Returns
    -------
        a formatted string ready to send, with markdown syntax
    """

    output = ['# Server Status Overview\n']
    for server, status in statusmap.items():
        output.append(f'# {server} is running' if status else f'> {server} is offline')
    return '\n'.join(output)