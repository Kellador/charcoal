import json
import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, List, Tuple

log = logging.getLogger(f'spiffy-mc.{__name__}')


class Store(MutableMapping):
    """MutableMapping with functions to load from, and save to, json files.
    """

    def __init__(
        self,
        file: Path,
        boot_store: Path | None = None,
        load: bool = True,
        ensure_entries: List[Tuple[str, Any]] | None = None,
    ):
        """init

        Parameters
        ----------
        file
            path to persistent file,
            will become a .json file even if given another suffix
        boot_store, optional
            path to a .json file, copied on first load, by default None
        load, optional
            whether to automattically attempt loading from given 'file' on init, by default True
        ensure_entries, optional
            list of (key, value) tuples that will be added to the mapping on init,
            usable as alternative or in addition to 'boot_store', by default None
        """
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
                    log.debug(f'Initialized from {self.boot_store}.')
                    return
            else:
                self.store = {}
                log.debug('No boot store defined, initializing as empty dictionary.')
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
            log.debug(f'{self.file} loaded.')

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
