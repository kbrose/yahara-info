import requests
import pandas as pd
from datetime import datetime, timedelta

from typing import Union

def scrape(start: datetime, end: Union[datetime, None]=None) -> pd.DataFrame:
    """
    Scrape the lake levels from start to end. If end is not
    specified, default to tomorrow (in your computer's timezone).

    The returned pandas Dataframe is the unmodified table as you would
    see on the website, no cleaning is done here.

    The site appears to use 0s as null values, and there are definitely
    outliers that appear to be incorrect measurements.
    """
    date_format = '%m/%d/%Y'
    url = 'https://lwrd.countyofdane.com/chartlakelevels/Tabular'
    if end is None:
        end_str = (datetime.now() + timedelta(days=1)).strftime(date_format)
    else:
        end_str = end.strftime(date_format)
    start_str = start.strftime(date_format)
    r = requests.post(url, data={'Start': start_str, 'End': end_str})
    dfs = pd.read_html(r.text)
    if len(dfs) != 1:
        raise ValueError(f'Expected one table in response, found {len(dfs)}.')
    df = dfs[0]
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', drop=True, inplace=True)
    return df
