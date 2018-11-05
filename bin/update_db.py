#!/usr/bin/env python
import argparse
from datetime import datetime as dt

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Full scrape.')
    return parser


def main(full_scrape):
    url = 'https://madison-lake-levels.herokuapp.com/'
    if full_scrape:
        start = dt(2007, 10, 1).isoformat()
        end = dt.utcnow().isoformat()
        requests.post(url + f'/update/{start}/{end}')
    else:
        requests.post(url + f'/update')


if __name__ == '__main__':
    p = build_parser()
    args = p.parse_args()
    main(args.full)
