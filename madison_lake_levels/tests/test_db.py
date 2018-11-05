from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from madison_lake_levels import db


class Test_DB():
    def setup_class(self):
        self.test_db_filepath = Path(__file__).parent / 'test.db'
        columns = ['mendota', 'monona', 'waubesa', 'kegonsa']
        self.example_df = pd.DataFrame(
            [{c: float(i) for i, c in enumerate(columns)}],
            index=pd.to_datetime(['2018-10-01T00:00'])
        )
        self.example_df = self.example_df[columns]

    def setup_method(self):
        self._delete_test_db_file()

    def teardown_method(self):
        self._delete_test_db_file()

    def _delete_test_db_file(self):
        try:
            self.test_db_filepath.unlink()
        except FileNotFoundError:
            pass

    def test_creation(self):
        db.LakeLevelDB(self.test_db_filepath)
        assert self.test_db_filepath.exists()

    def test_insertion(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        lldb.insert(self.example_df)
        assert len(lldb._cursor.execute('SELECT * FROM levels').fetchall()) == 1

    def test_to_df(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        lldb.insert(self.example_df)
        out_df = lldb.to_df()
        assert (out_df.values == self.example_df.values).all()

    def test_insert_non_unique_raises(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        lldb.insert(self.example_df)
        with pytest.raises(sqlite3.IntegrityError):
            lldb.insert(self.example_df)

    def test_insert_non_unique_ok_if_allowed(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        df = self.example_df.copy()
        lldb.insert(df)
        df['mendota'] = -1.0
        lldb.insert(df, replace=True)
        out_df = lldb.to_df()
        assert out_df['mendota'].size == 1
        assert out_df['mendota'].iloc[0] == -1.0

    def test_no_clear_does_not_clear(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        lldb.insert(self.example_df)
        del lldb
        lldb = db.LakeLevelDB(self.test_db_filepath)
        out_df = lldb.to_df()
        assert out_df.size > 0

    def test_clear_clears(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        lldb.insert(self.example_df)
        del lldb
        lldb = db.LakeLevelDB(self.test_db_filepath, clear=True)
        out_df = lldb.to_df()
        assert out_df.size == 0

    def test_most_recent(self):
        lldb = db.LakeLevelDB(self.test_db_filepath)
        lldb.insert(self.example_df)
        assert lldb.most_recent().size == 4
