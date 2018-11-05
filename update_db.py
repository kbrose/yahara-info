#!/usr/bin/env python

from datetime import datetime

import madison_lake_levels as mll


def main():
    lldb = mll.db.LakeLevelDB(mll.db.default_db_filepath)
    most_recent_time = lldb.most_recent().index[0].to_pydatetime()
    mll.scrape.backfill(most_recent_time, datetime.utcnow(), lldb)


if __name__ == '__main__':
    main()
