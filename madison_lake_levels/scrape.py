import json
import io
import functools
import time

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from typing import Union

from .db import LakeLevelDB

# See https://waterdata.usgs.gov/wi/nwis/current/?type=dane&group_key=NONE
lake_name_to_usgs_site_num = {
    'MENDOTA': '05428000',
    'MONONA': '05429000',
    'WAUBESA': '05429485',
    'KEGONSA': '425715089164700'
}


def _format_usgs_lake_names(name):
    return name.split()[1].lower()


def scrape(start: Union[datetime, None]=None,
           end: Union[datetime, None]=None) -> pd.DataFrame:
    """
    Scrape Madison lake heights from public USGS data.
    Heights reported are the gage height + datum elevation.

    Inputs
    ------
    start : datetime | None
        Starting timestamp to collect data from. If `None`
        then `end` must also be `None`, and in this case just the most
        recent sample is returned.
    end : datetime | None
        End timestamp to collect data to. If `None` then go to
        the most recently reported data.

    Returns
    -------
    df : pandas.DataFrame
        A pandas dataframe of lake heights. Each lake has a column.
    """
    date_format = '%Y-%m-%d'
    if start is None:
        start_arg = ''
    else:
        start_arg = '&startDT={}'.format(start.strftime(date_format))

    if end is None:
        end_arg = ''
    elif start is None:
        raise ValueError('If start is None, then end must be None too.')
    else:
        end_arg = '&endDT={}'.format(end.strftime(date_format))

    sites = ','.join(lake_name_to_usgs_site_num.values())

    base_url = 'http://waterservices.usgs.gov/nwis/iv/?'
    url_args = f'&sites={sites}&format=json{start_arg}{end_arg}'

    r = requests.post(base_url + url_args)
    d = json.loads(r.text)
    df = pd.DataFrame({})
    for ts in d['value']['timeSeries']:
        lake_name = _format_usgs_lake_names(ts['sourceInfo']['siteName'])
        values = ts['values'][0]['value']
        gage_heights = [float(v['value']) for v in values]
        times = [v['dateTime'] for v in values]
        assert len(times) == len(gage_heights)
        df[lake_name] = pd.Series(dict(zip(times, gage_heights)))

    for lake_name in lake_name_to_usgs_site_num.keys():
        if lake_name.lower() not in df.columns:
            df[lake_name.lower()] = np.nan

    datum = get_datum_elevation(sites)

    for name, datum_elevation in datum['alt_va'].iteritems():
        df[name] += datum_elevation

    df.index = pd.to_datetime(df.index, utc=True)

    return df


@functools.lru_cache(maxsize=50)
def get_datum_elevation(sites: str) -> pd.DataFrame:
    """
    Given a comma separated list of site numbers, return the datum
    elevations of those sites. From what I can tell, this is the base
    height of the sensor that records lake levls, so the total height
    of the lake level is the sum of the datum elevation and the sensor reading.

    This function is cached since the rate at which these values change has
    historically been on the order of decades.

    Inputs
    ----------
    sites : str
        Comma separated list of site numbers. See `lake_name_to_usgs_site_num`.

    Returns
    -------
    datum : pandas.DataFrame
        A dataframe of datum elevations. Rows are keyed off lake name,
        and the main column of interest will be `'alt_va'`.
    """
    base_datum_url = 'https://waterservices.usgs.gov/nwis/site/?'
    datum_url_args = f'&sites={sites}&format=rdb'
    r = requests.post(base_datum_url + datum_url_args)
    no_hash = '\n'.join(l for l in r.text.split('\n') if not l.startswith('#'))
    datum = pd.read_csv(
        io.StringIO(no_hash),
        delimiter='\t'
    )
    # first row is not useful info
    datum = datum.iloc[1:]
    datum['station_nm'] = datum['station_nm'].apply(_format_usgs_lake_names)
    datum.set_index('station_nm', drop=True, inplace=True)
    datum['alt_va'] = datum['alt_va'].apply(float)
    return datum


def backfill(start: datetime, end: datetime, lldb: LakeLevelDB, verbose=False):
    step = timedelta(days=30)
    if verbose:
        print(f'Starting backfill from {start} to {end}')
    while start < end:
        # be kind to the servers
        time.sleep(0.01)
        df = scrape(start, min(start + step, end))
        lldb.insert(df, replace=True)
        start += step
        if verbose:
            print(f' Scraped starting at {start}')
    if verbose:
        print(' Done.')
