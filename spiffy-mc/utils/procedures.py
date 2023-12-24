import asyncio
import logging

log = logging.getLogger(f'spiffy-mc.{__name__}')


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


def execute_procedures(serverdir: Path, procedures: dict[str, Any]):
    """Execute procedures, if valid.

    Parameters
    ----------
    procedures
        a dict of procedures <format wip>
    """

    for k, v in procedures.items():
        match k:
            case 'neutralize':
                log.info('Executing special procedure: neutralize ...')
                for target in v:
                    tpath: Path = serverdir / target
                    if tpath.exists():
                        tpath.replace(tpath.with_suffix(f'{tpath.suffix}.neutralized'))
                        log.info(f'Neutralized "{tpath}"!')
            case _:
                pass