import logging
from pathlib import Path
from typing import Callable

log = logging.getLogger(f'spiffy-mc.{__name__}')


class LoggedException(Exception):
    def __init__(self, message: str, log_func: Callable) -> None:
        self.message = message
        self.log_func = log_func
        super().__init__(self.message)

    def log_this(self):
        self.log_func(self.message)


class ServerNotFound(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(f'{sdir} does not exist', log.warning)


class NoInvocation(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} does not contain a \'spiffy_invocation\' file', log.warning
        )


class ParentDirMissing(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(f'{sdir} does not exist!', log.warning)


class NothingToBackup(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} contains no \'world\' directory or \'world\' isn\'t included, '
            'and it has no \'charcoal_backup\' file specifying other directories to back up',
            log.warning,
        )


class Untracked(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} exists, but is untracked by charcoal (no \'charcoal_enabled\' or \'charcoal_disabled\' file present)',
            log.warning,
        )


class ServerStartFailed(LoggedException):
    def __init__(self, server: str, message: str) -> None:
        super().__init__(f'starting of {server} has failed!', log.error)


class ServerStopFailed(LoggedException):
    def __init__(self, server: str, message: str) -> None:
        super().__init__(f'stopping of {server} has failed!', log.error)


class ServerRestartFailed(LoggedException):
    def __init__(self, server: str, message: str) -> None:
        super().__init__(f'restart of {server} has failed!', log.error)


class TerminationFailed(LoggedException):
    def __init__(self, server: str) -> None:
        super().__init__(f'termination of {server} failed!', log.error)


class ServerPropertiesMissing(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(f'{sdir} has no \'server.properties\'', log.warning)


class RconAuthFailure(LoggedException):
    def __init__(self, server: str, details: str) -> None:
        super().__init__(
            f'RCON Authentication with {server} failed, {details}', log.error
        )


class RconNotEnabled(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(f'RCON is not enabled for {sdir}', log.warning)


class RconLoginDetailsMissing(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} has no port and/or password defined for RCON', log.warning
        )


class RconSettingsError(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} is missing some RCON setting entries, is \'server.properties\' corrupted?',
            log.error,
        )


class OldReport(LoggedException):
    def __init__(self, sdir: Path, age: int) -> None:
        super().__init__(
            f'Latest crashreport found in {sdir} is older than {age} hours!',
            log.warning,
        )
        
        
class NoReportDirectory(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} contains no crash-reports directory',
            log.warning,
        )
        
        
class NoReports(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} has no crash-reports',
            log.warning,
        )


class NoProcedures(LoggedException):
    def __init__(self, sdir: Path) -> None:
        super().__init__(
            f'{sdir} contains no \'charcoal_procedures\' file', log.warning
        )
