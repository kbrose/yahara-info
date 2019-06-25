from datetime import datetime as dt
from datetime import timedelta

from madison_lake_levels import scrape


class Test_Scrape():
    @staticmethod
    def test_most_recent():
        df = scrape.scrape()
        assert df.shape == (1, 4)

    @staticmethod
    def test_start_no_end():
        # cannot assert for correctness, only assure no errors are raised
        scrape.scrape(dt.now() - timedelta(hours=25))

    # The USGS appears to have revised these values, and the test now fails.
    # @staticmethod
    # def test_known_null():
    #     # This period had an equipment malfunction, reporting values of
    #     # -999999
    #     df = scrape.scrape(dt(2019, 2, 26), dt(2019, 2, 27))
    #     assert df['mendota'].isnull().all()
