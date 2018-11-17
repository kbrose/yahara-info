import os
import gc

import psycopg2
import pandas as pd
import pytest

from madison_lake_levels import db


class Test_DB():
    def setup_class(self):
        self.test_db_name = 'madisonlakes_test'
        user = os.getenv('TEST_DB_USER', os.getenv('USER'))
        self.db_config = {
            'database': self.test_db_name,
            'user': user
        }
        pw = os.getenv('TEST_DB_PW')
        if pw is not None:
            self.db_config['password'] = pw

        self._templates_conn = psycopg2.connect(
            database='template1', user=user
        )
        self._templates_conn.autocommit = True
        self._templates_curr = self._templates_conn.cursor()

        columns = ['mendota', 'monona', 'waubesa', 'kegonsa']
        self.example_df = pd.DataFrame(
            [{c: float(i) for i, c in enumerate(columns)}],
            index=pd.to_datetime(['2018-10-01'])
        )
        self.example_df = self.example_df[columns]

    def setup_method(self):
        self._drop_test_db()
        self._templates_curr.execute(f"CREATE DATABASE {self.test_db_name};")

    def teardown_method(self):
        self._drop_test_db()

    def _drop_test_db(self):
        gc.collect()
        try:
            self._templates_curr.execute(f"DROP DATABASE {self.test_db_name};")
        except psycopg2.ProgrammingError:
            pass

    def test_creation(self):
        db.LakeLevelDB(**self.db_config)

    def test_insertion(self):
        lldb = db.LakeLevelDB(**self.db_config)
        lldb.insert(self.example_df)
        lldb._cursor.execute('SELECT * FROM levels')
        assert len(lldb._cursor.fetchall()) == 1

    def test_to_df(self):
        lldb = db.LakeLevelDB(**self.db_config)
        lldb.insert(self.example_df)
        out_df = lldb.to_df()
        assert (out_df.values == self.example_df.values).all()

    def test_insert_non_unique_raises(self):
        lldb = db.LakeLevelDB(**self.db_config)
        lldb.insert(self.example_df)
        with pytest.raises(psycopg2.IntegrityError):
            lldb.insert(self.example_df, replace=False)

    def test_insert_non_unique_ok_if_allowed(self):
        lldb = db.LakeLevelDB(**self.db_config)
        df = self.example_df.copy()
        lldb.insert(df)
        df['mendota'] = 10.0
        lldb.insert(df, replace=True)
        out_df = lldb.to_df()
        assert out_df['mendota'].size == 1
        assert out_df['mendota'].iloc[0] == 10.0

    def test_most_recent(self):
        lldb = db.LakeLevelDB(**self.db_config)
        lldb.insert(self.example_df)
        assert lldb.most_recent().size == 4
