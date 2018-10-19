import json
import io

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
        end = datetime.now() + timedelta(days=1)
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


def _format_usgs_lake_names(name):
    return name.split()[1].lower()


def usgs(start: Union[datetime, None]=None, end: Union[datetime, None]=None) -> pd.DataFrame:
    """
    TODO
    """
    date_format = '%Y-%m-%d'
    if start is None:
        start_arg = ''
    else:
        start_arg = '&startDT={}'.format(start.strftime(date_format))

    if end is None:
        end_arg = ''
    else:
        end_arg = '&endDT={}'.format(end.strftime(date_format))

    # See https://waterdata.usgs.gov/wi/nwis/current/?type=dane&group_key=NONE
    lake_name_to_usgs_site_num = {
        'MENDOTA': '05428000',
        'MONONA': '05429000',
        'WAUBESA': '05429485',
        'KEGONSA': '425715089164700'
    }
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
    for name, datum_elevation in datum['alt_va'].iteritems():
        df[name] += datum_elevation

    df.index = pd.to_datetime(df.index, utc=True)

    return df
