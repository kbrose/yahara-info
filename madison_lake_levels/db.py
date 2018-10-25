from pathlib import Path
import sqlite3
from typing import Union

import pandas as pd

class LakeLevelDB():
    def __init__(self, db_filepath: Union[str, None]=None):
        if db_filepath is None:
            db_filepath = Path(__file__).parent / 'data' / 'lake_levels.db'
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

    def insert(self, df: pd.DataFrame):
        """
        Insert a dataframe of data into the database.

        Inputs
        ------
        df : pd.DataFrame
            DataFrame with a datetime row index and four columns
            with names ['mendota', 'monona', 'waubesa', 'kegonsa']
        """
        df = df[['mendota', 'monona', 'waubesa', 'kegonsa']]
        cmd = """INSERT INTO levels (
            datetime, mendota, monona, waubesa, kegonsa
        )
        VALUES (?, ?, ?, ?, ?);
        """
        for time, row in df.iterrows():
            time = time.isoformat()
            self._cursor.execute(cmd, [time] + row.tolist())
        self._conn.commit()

    def to_df(self) -> pd.DataFrame:
        """
        Return the database as a pandas DataFrame.
        """
        return pd.read_sql_query(
            'SELECT * FROM levels',
            self._conn
        ).set_index('datetime', drop=True)
