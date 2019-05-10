#!/usr/bin/env python3
"""
Author: @azjps
Run visidata PandasSheet on a dataframe with columns
of different datatypes and a length controlled by
the command-line option --repeat. The default size
of the loaded dataframe is 1 million rows.
"""

import argparse

import pandas as pd
import numpy as np

import visidata

visidata.options.disp_date_fmt = "%Y%m%d %H:%M:%S.%f"

if __name__ == "__main__":
    group_count = 10
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repeat", default=100000, type=int,
        help="Number of times to repeat rows, total # of rows = {} * repeat. "
             "Default=100000 for a million rows total."
             .format(group_count)
    )
    args = parser.parse_args()

    repeat_count = args.repeat
    df = pd.DataFrame({
        "date1": pd.date_range(start="2020/01/01", freq="D", periods=group_count),
        "date2": pd.date_range(start="2020/01/01 02:15:30.012345", freq="D", periods=group_count),
        "int1": np.arange(group_count),
        "float1": np.arange(group_count) + 0.5,
        "cat1": [str(i) for i in np.arange(group_count)],
        "repeat1": np.repeat(1, group_count),
    })
    df["cat1"] = df["cat1"].astype("category")
    df["timedelta1"] = df["date1"].diff()
    # Repeat so that we are a significant amount of rows
    big_df = df.iloc[np.repeat(np.arange(0, group_count), repeat_count)]
    big_df = big_df.copy().reset_index(drop=True)
    # To make the frequencies a bit more interesting, shift the int2 & date2 columns 20% "upwards"
    big_df["int2"] = big_df["int1"].shift(-repeat_count // 5)
    big_df["date2"] = big_df["date2"].shift(-repeat_count // 5)
    big_df["int3"] = big_df["int1"].shift(repeat_count // 5)

    visidata.run(visidata.PandasSheet('pandas', source=big_df))
