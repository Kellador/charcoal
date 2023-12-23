import json
import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, List, Tuple

log = logging.getLogger(__name__)


class Settings:
    def __init__(
        self, parent_directory: str, backup_directory: str, backup_maxAge: int
    ) -> None:
        self.parent_directory = Path(parent_directory)
        self.backup_directory = Path(backup_directory)
        self.backup_maxAge = backup_maxAge


class Store(MutableMapping):
    """MutableMapping for dynamic data storage, with async capabilities;
    Parses data to and from json files.
    """

    def __init__(
        self,
        file: Path,
        boot_store: Path | None = None,
        load: bool = True,
        ensure_entries: List[Tuple[str, Any]] | None = None,
    ):
        self.file = file.with_suffix('.json')
        self.boot_store = boot_store
        if load:
            try:
                self.load()
            except:
                raise
        if ensure_entries:
            for k, v in ensure_entries:
                if k not in self.store:
                    self.store[k] = v

    def load(self):
        if not self.file.exists():
            log.info(f'{self.file} does not exist yet.')
            self.file.parent.mkdir(parents=True, exist_ok=True)
            if self.boot_store:
                try:
                    with self.boot_store.open() as icf:
                        self.store = json.load(icf)
                except OSError:
                    log.critical(f'{self.boot_store} could not be loaded!')
                    raise
                except json.JSONDecodeError:
                    log.critical(f'{self.boot_store} does not contain valid json!')
                    raise
                else:
                    log.info(f'Initialized from {self.boot_store}.')
                    return
            else:
                self.store = {}
                log.info('No boot store defined, initializing as empty dictionary.')
                return

        try:
            with self.file.open() as cf:
                self.store = json.load(cf)
        except OSError:
            log.critical(f'Could not load {self.file}!')
            raise
        except json.JSONDecodeError:
            log.critical(f'{self.file} does not contain valid json!')
            raise
        else:
            log.info(f'{self.file} loaded.')

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        tmpfile = self.file.with_suffix('.tmp')
        with tmpfile.open('w') as tmp:
            json.dump(self.store.copy(), tmp)
        tmpfile.replace(self.file)

    def __getitem__(self, key):
        return self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]
