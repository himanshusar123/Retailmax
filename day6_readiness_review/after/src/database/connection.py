"""SQLite connection manager using context manager protocol.

Demonstrates safe connection lifetimes and Module 2 type hinting.
"""

import sqlite3
from types import TracebackType


class SQLiteConnectionManager:
    """Context manager for SQLite connections.

    Guarantees cleanup and transaction safety.
    """

    def __init__(self, db_path: str) -> None:
        """Initializes with the target database file path."""
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        """Establishes connection and begins transaction boundary."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commits on success, rolls back on error, and closes connection."""
        if self.connection:
            if exc_type is not None:
                self.connection.rollback()
            else:
                self.connection.commit()
            self.connection.close()
