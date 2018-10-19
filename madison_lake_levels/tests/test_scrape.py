from datetime import datetime as dt
from datetime import timedelta

import pytest

from madison_lake_levels import scrape


class Test_Scrape():
    @staticmethod
    def test_most_recent():
        df = scrape.scrape()
        assert df.shape == (1, 4)

    @staticmethod
    def test_start_no_end():
        # cannot assert for correctness, only assure no errors are raised
        scrape.scrape(dt.now() - timedelta(hours=1))
