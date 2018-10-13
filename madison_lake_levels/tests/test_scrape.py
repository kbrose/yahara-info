from datetime import datetime as dt
from unittest import mock

import pytest

from madison_lake_levels import scrape

# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.text = ''
            self.status_code = 200
    return MockResponse()

class Test_Scrape():
    @staticmethod
    def test_small_timespan():
        df = scrape.scrape(dt(2018, 10, 1), dt(2018, 10, 8))
        assert df.shape[0] == 8

    @staticmethod
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_bad_response(mock_post):
        with pytest.raises(ValueError):
            df = scrape.scrape(dt(2018, 10, 1))
