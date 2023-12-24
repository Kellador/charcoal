import asyncio
import logging

log = logging.getLogger(f'spiffy-mc.{__name__}')


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


def backup(cfg: 'Settings', server: str, specific_path: str | None = None):
    """Perform backup of a given server.

    Backups always include the 'world' directory if it exists,
    further directories may be specified in a 'spiffy_backup' file
    inside the server's directory;

    Alternatively specific backups may be performed by calling this
    function with the 'specific_path' parameter pointing to a
    given servers subdirectory or file to back up instead.
    """

    try:
        server_path = find_server(cfg.parent_directory, server)
    except (ParentDirMissing, ServerNotFound) as e:
        e.log_this()
        return
    except NoInvocation:
        pass

    if specific_path:
        _source = server_path / specific_path
        if _source.exists():
            specification = {
                'include': [_source],
                'exclude': [],
            }
        else:
            try:
                Path(specific_path).relative_to(server_path)
            except ValueError:
                log.error(f'{specific_path} is not a subpath of {server_path}!')
                return
            else:
                specification = {
                    'include': [specific_path],
                    'exclude': [],
                }
    else:
        try:
            specification = get_backup(server_path)
        except NothingToBackup as e:
            e.log_this()
            return
        else:
            if not specification['include']:
                log.warning(f'Back up job for {server} failed, nothing to back up!')
                return

    log.info(f'Starting backup for {server}...')
    if isUp(server):
        log.info(f'{server} is running, announcing backup and toggling save!')
        screenCmd(server, 'Starting Backup!', 'save-off', 'save-all')
        sleep(10)

    now = time()
    now_str = datetime.now().strftime('%Y.%m.%d_%H_%M_%S')

    backup_location = cfg.backup_directory / server
    backup_location.mkdir(parents=True, exist_ok=True)

    log.info('Cleaning up backups...')

    for d in backup_location.iterdir():
        if d.is_dir() and not d.name.startswith('.'):
            if d.stat().st_mtime < now - (cfg.backup_maxAge * 60):
                for e in d.iterdir():
                    if e.is_file():
                        e.unlink()
                        log.info(f'Deleted \'{e}\'')
                    if e.is_dir():
                        log.warning(f'Found directory {e.name} in {d} during cleanup!')
                        log.warning(
                            f'Please remove {e} manually if it is no longer needed!'
                        )
                try:
                    d.rmdir()
                except OSError:
                    log.warning(
                        f'Outdated backup directory {d} could not be fully removed!'
                    )
                    log.warning(
                        'This is likely because an unpacked backup still exists within.'
                    )
                else:
                    log.info(f'Cleaned up outdated backup directory \'{d}\'')

    log.info(f'Creating backup(s) specified for {server}...')

    target_path = backup_location / f'{now_str}'
    target_path.mkdir(exist_ok=True)

    os.chdir(target_path)

    for source_path in specification['include']:
        log.info(f'Backing up \'{source_path}\'...')
        try:
            filename = source_path.relative_to(server_path)
        except ValueError:
            log.critical(f'\'{source_path}\' is not a subpath of the specified server!')
            log.error(
                'This should not be possible. Backup aborted! Please contact someone!'
            )
            return
        else:
            filename = '.'.join(filename.parts)

        exclusions = [
            f'{p.relative_to(server_path)}'
            for p in specification['exclude']
            if p.is_relative_to(source_path)
        ]

        def _filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
            if any(tarinfo.name.startswith(ex) for ex in exclusions):
                log.debug(f'excluded: {tarinfo.name}')
                return None
            else:
                return tarinfo

        with tarfile.open(f'{filename}.tar.gz', 'w:gz') as tf:
            if exclusions:
                tf.add(source_path, source_path.name, filter=_filter)
            else:
                tf.add(source_path, source_path.name)
        log.info(f'\'{source_path}\' backed up!')

    log.info(f'Backup(s) created for {server}!')

    if isUp(server):
        log.info(f'{server} is running, re-enabling save!')
        screenCmd(server, 'save-on', 'Backup complete!')
