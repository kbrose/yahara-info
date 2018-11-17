import os
from functools import wraps

import psycopg2
import pandas as pd


def _rollback_or_commit(f):
    @wraps(f)
    def function_wrapper(self, *args, **kwargs):
        """ function_wrapper of greeting """
        try:
            ret = f(self, *args, **kwargs)
        except psycopg2.Error:
            self._conn.rollback()
            raise
        self._conn.commit()
        return ret

    return function_wrapper


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

    @_rollback_or_commit
    def insert(self, df: pd.DataFrame, replace=True):
        """
        Insert a dataframe of data into the database.

        Inputs
        ------
        df : pd.DataFrame
            DataFrame with a datetime row index and four columns
            with names ['mendota', 'monona', 'waubesa', 'kegonsa']
        replace : bool
            If truthy, some values may be replaced if the value in
            df is higher.
        """
        df = df[self._columns[1:]]

        insert_cmd = """INSERT INTO levels (
            datetime, mendota, monona, waubesa, kegonsa
        )
        VALUES (%s, %s, %s, %s, %s);
        """

        update_cmd_static = """UPDATE levels
        SET {columns}
        WHERE datetime=%s;
        """

        select_cmd = "SELECT * FROM levels WHERE datetime=%s;"

        for time, row in df.iterrows():
            time = time.to_pydatetime()
            if replace:
                self._cursor.execute(select_cmd, (time,))
                result = self._cursor.fetchone()
                update_cmd = update_cmd_static
                if result:
                    for lake, height in zip(self._columns[1:], result[1:]):
                        if height < row[lake]:
                            update_cmd = update_cmd.format(
                                columns=f'{lake}={row[lake]}, {{columns}}'
                            )
                    update_cmd = update_cmd.replace(', {columns}', '')
                    if 'SET {columns}' not in update_cmd:
                        self._cursor.execute(update_cmd, (time,))
                    # else row already existed but no updates need to be made
                else:
                    self._cursor.execute(insert_cmd, [time] + row.tolist())
            else:
                self._cursor.execute(insert_cmd, [time] + row.tolist())

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


def config_from_env():
    config = {
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
    }
    return config
