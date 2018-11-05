#!/usr/bin/env python
import argparse

from datetime import datetime as dt

import madison_lake_levels as mll


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Full scrape.')
    return parser


def main(full_scrape):
    lldb = mll.db.LakeLevelDB(mll.db.default_db_filepath)
    if full_scrape:
        mll.scrape.backfill(dt(2007, 10, 1), dt.utcnow(), lldb, True)
    else:
        most_recent_time = lldb.most_recent().index[0].to_pydatetime()
        mll.scrape.backfill(most_recent_time, dt.utcnow(), lldb, True)


if __name__ == '__main__':
    p = build_parser()
    args = p.parse_args()
    main(args.full)
