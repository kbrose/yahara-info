from pathlib import Path
import sqlite3
from typing import Union

import pandas as pd

default_db_filepath = Path(__file__).parent / 'data' / 'lake_levels.db'

class LakeLevelDB():
    def __init__(self, db_filepath: str):
        """
        Create a lake level database.

        If the file located at db_filepath exists, it is assumed to be
        a correctly formatted database.

        Inputs
        ------
        db_filepath : str
            The filepath to where the database should be stored.
            A good option for this is `default_db_filepath`.
        """
        self._db_filepath = db_filepath
        self._conn = sqlite3.connect(db_filepath)
        self._cursor = self._conn.cursor()

        self._create_if_nonexistent()

    def _create_if_nonexistent(self):
        cmd = "SELECT name FROM sqlite_master WHERE type='table' AND name='levels'"
        if self._cursor.execute(cmd).fetchone() is None:
            cmd = """CREATE TABLE levels (
                datetime text PRIMARY KEY,
                mendota real,
                monona real,
                waubesa real,
                kegonsa real
            )
            """
            self._cursor.execute(cmd)
            self._conn.commit()

    def insert(self, df: pd.DataFrame, replace=False):
        """
        Insert a dataframe of data into the database.

        Inputs
        ------
        df : pd.DataFrame
            DataFrame with a datetime row index and four columns
            with names ['mendota', 'monona', 'waubesa', 'kegonsa']
        replace
            If truthy, any datetime conflicts will be updated treating
            the input df as correct. Otherwise, conflicts will result
            in sqlite3.IntegrityError
        """
        df = df[['mendota', 'monona', 'waubesa', 'kegonsa']]
        cmd = """INSERT{replacer} INTO levels (
            datetime, mendota, monona, waubesa, kegonsa
        )
        VALUES (?, ?, ?, ?, ?);
        """.format(replacer=' OR REPLACE' if replace else '')
        for time, row in df.iterrows():
            time = time.isoformat()
            self._cursor.execute(cmd, [time] + row.tolist())
        self._conn.commit()

    def to_df(self) -> pd.DataFrame:
        """
        Return the database as a pandas DataFrame.

        Not for the faint of heart, nor faint of RAM.
        """
        return pd.read_sql_query(
            'SELECT * FROM levels',
            self._conn
        ).set_index('datetime', drop=True)
