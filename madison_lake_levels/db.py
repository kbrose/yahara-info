from pathlib import Path

import psycopg2
import pandas as pd

default_db_filepath = Path(__file__).parent / 'data' / 'lake_levels.db'


class LakeLevelDB():
    def __init__(self, **config):
        """
        Connect to a lake level database.

        Arguments in **config will be passed directly to `psycopg2.connect`.
        """
        self._conn = psycopg2.connect(**config)
        self._cursor = self._conn.cursor()
        self._columns = ['datetime', 'mendota', 'monona', 'waubesa', 'kegonsa']

        self._create_if_nonexistent()

    def _create_if_nonexistent(self):
        cmd = ("SELECT EXISTS ("
               " SELECT 1"
               " FROM  information_schema.tables"
               " WHERE table_name = 'levels');")
        self._cursor.execute(cmd)
        if not self._cursor.fetchone()[0]:
            cmd = """CREATE TABLE levels (
                datetime date PRIMARY KEY,
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
        VALUES (%s, %s, %s, %s, %s);
        """
        for time, row in df.iterrows():
            time = time.isoformat()
            self._cursor.execute(cmd, [time] + row.tolist())
        self._conn.commit()

    def to_df(self) -> pd.DataFrame:
        """
        Return the database as a pandas DataFrame.

        Not for the faint of heart, nor faint of RAM.
        """
        df = pd.read_sql_query(
            'SELECT * FROM levels',
            self._conn
        ).set_index('datetime', drop=True)
        df.index = pd.to_datetime(df.index)
        return df

    def most_recent(self) -> dict:
        """
        Return the most recent reading.
        """
        cmd = "SELECT * FROM levels ORDER BY datetime LIMIT 1"
        df = pd.read_sql_query(cmd, self._conn)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime', drop=True)
        return df
