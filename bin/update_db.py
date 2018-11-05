#!/usr/bin/env python
import argparse
from datetime import datetime as dt
from datetime import timedelta

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Full scrape.')
    return parser


def main(full_scrape):
    url = 'https://madison-lake-levels.herokuapp.com/'
    if full_scrape:
        start_dt = dt(2007, 10, 1)
        end_dt = dt.utcnow()
        step = timedelta(days=30)
        while start_dt < end_dt:
            start = start_dt.isoformat()
            end = min(start_dt + step, end_dt).isoformat()
            requests.post(url + f'/update/{start}/{end}')
            start_dt += step
    else:
        requests.post(url + f'/update')


if __name__ == '__main__':
    p = build_parser()
    args = p.parse_args()
    main(args.full)
