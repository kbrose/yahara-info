from datetime import datetime as dt
from datetime import timedelta

import pytest

from madison_lake_levels import required_levels


class Test_Required_Levels():
    @staticmethod
    def test_levels():
        df = required_levels.required_levels
        assert df.shape == (4, 3)
