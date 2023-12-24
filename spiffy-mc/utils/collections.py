import time
from collections import OrderedDict
from pathlib import Path


class Settings:
    def __init__(
        self, parent_directory: str, backup_directory: str, backup_maxAge: int
    ) -> None:
        self.parent_directory = Path(parent_directory)
        self.backup_directory = Path(backup_directory)
        self.backup_maxAge = backup_maxAge
        

class SimpleTTLDict(OrderedDict):
    """Super simple implementation of an OrderedDict with expiring
    items.

    Only deletes items that have outlived their ttl when new items
    are inserted.
    """
    def __init__(self, ttl_seconds=360):
        assert ttl_seconds >= 0

        super().__init__(self)
        self.ttl = ttl_seconds

    def _expire(self):
        """Deletes all dict items that have outlived their ttl."""
        now = int(time.time())
        while self:
            (key, (value, date)) = super().popitem(last=False)
            if now - date > self.ttl:
                continue
            else:
                super().__setitem__(key, (value, date))
                super().move_to_end(key, last=False)
                break

    def __setitem__(self, key, value):
        """Set d[key] to (value, date), where date is its creation time.

        Also removes all expired entries.
        """
        self._expire()
        super().__setitem__(key, (value, int(time.time())))
        super().move_to_end(key)

    def getvalue(self, key):
        """Gets the value from a (value, date) tuple of a given key."""
        return super().__getitem__(key)[0]

    def find(self, predicate):
        """Finds and returns the first value that satisifies a given
        predicate."""
        for (value, _) in reversed(self.values()):
            if predicate(value):
                return value


class SizedDict(OrderedDict):
    """Super simple implementation of an OrderedDict with a fixed size.

    Adding a new item after maximum size has been reached removes
    the oldest item to make room.
    """

    def __init__(self, max_size=100):
        assert max_size >= 1

        super().__init__(self)
        self.max_size = max_size

    def __setitem__(self, key, value):
        """Sets item and moves it to the end (in case of updates)"""
        super().__setitem__(key, value)
        super().move_to_end(key)
        self._prune()

    def _prune(self):
        """Prune any items out of max_size range."""
        while len(self) > self.max_size:
            self.popitem(last=False)

    def find(self, predicate):
        """Finds and returns the first value that satisifies a given
        predicate, LIFO style."""

        for value in reversed(self.values()):
            if predicate(value):
                return value
        else:
            return None
