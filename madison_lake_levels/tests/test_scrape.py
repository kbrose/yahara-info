from datetime import datetime as dt
from unittest import mock

import pytest

from madison_lake_levels import scrape

# This method will be used by the mock to replace requests.post
def mocked_requests_post_no_tables(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.text = ''
            self.status_code = 200
    return MockResponse()


def mocked_requests_post_extra_tables(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.text = """
            <html>
            <table class="table table-bordered table-striped table-condensed">
                <thead>
                <tr>
                <th>Date</th>
                <th>Mendota</th>
                <th>Monona</th>
                <th>Waubesa</th>
                <th>Kegonsa</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>10/1/2018</td>
                    <td>851.37</td>
                    <td>847.53</td>
                    <td>846.81</td>
                    <td>844.48</td>
                </tr>
            </table>
            <table class="table table-bordered table-striped table-condensed">
                <thead>
                <tr>
                <th>Date</th>
                <th>Mendota</th>
                <th>Monona</th>
                <th>Waubesa</th>
                <th>Kegonsa</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>10/1/2018</td>
                    <td>851.37</td>
                    <td>847.53</td>
                    <td>846.81</td>
                    <td>844.48</td>
                </tr>
            </table>
            </html>
            """
            self.status_code = 200
    return MockResponse()


class Test_Scrape():
    @staticmethod
    def test_small_timespan():
        df = scrape.scrape(dt(2018, 10, 1), dt(2018, 10, 8))
        assert df.shape[0] == 8

    @staticmethod
    @mock.patch('requests.post', side_effect=mocked_requests_post_no_tables)
    def test_no_tables(mock_post):
        with pytest.raises(ValueError):
            df = scrape.scrape(dt(2018, 10, 1))

    @staticmethod
    @mock.patch('requests.post', side_effect=mocked_requests_post_extra_tables)
    def test_extra_tables(mock_post):
        with pytest.raises(ValueError):
            df = scrape.scrape(dt(2018, 10, 1))
