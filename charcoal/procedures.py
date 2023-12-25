import asyncio
import logging

log = logging.getLogger(f'spiffy-mc.{__name__}')


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