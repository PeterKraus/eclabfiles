#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Functions for converting EC-Lab file data to DataFrame, .csv and .xlsx.

Author:         Nicolas Vetsch (veni@empa.ch / vetschnicolas@gmail.com)
Organisation:   EMPA Dübendorf, Materials for Energy Conversion (501)
Date:           2021-10-18

"""
import argparse
import os
from typing import Union

import pandas as pd

from .mpr import parse_mpr
from .mps import parse_mps
from .mpt import parse_mpt


def _construct_path(other_path: str, ext: str) -> str:
    """Constructs a new file path from the given path and extension.

    Parameters
    ----------
    other_path
        The path to some file.
    ext
        The new extension to add to the other_path.

    Returns
    -------
    str
        A new filepath with the given extension.

    """
    head, tail = os.path.split(other_path)
    tail, __ = os.path.splitext(tail)
    this_path = os.path.join(head, tail+ext)
    return this_path


def parse(path: str) -> Union[list, dict]:
    """Parses an EC-Lab file.

    The function finds the file extension and tries to choose the
    correct parser.

    Parameters
    ----------
    path
        The path to an EC-Lab file (.mpt/.mpr/.mps)

    Returns
    -------
    list or dict
        The parsed file.

    """
    __, ext = os.path.splitext(path)
    if ext == '.mpt':
        parsed = parse_mpt(path)
    elif ext == '.mpr':
        parsed = parse_mpr(path)
    elif ext == '.mps':
        parsed = parse_mps(path)
    return parsed


def to_df(path: str) -> Union[pd.DataFrame, list[pd.DataFrame]]:
    """Extracts the data from an EC-Lab file and returns it as Pandas
    DataFrame(s)

    The function finds the file extension and tries to choose the
    correct parser. If the file is an .mps, returns a list of
    DataFrames.

    Parameters
    ----------
    path
        The path to an EC-Lab file (.mpt/.mpr/.mps)
    get_technique (optional)
        Whether to also get the technique name as parsed from the
        original file. Useful for the other file-writing functions.
        Defaults to False.

    Returns
    -------
    pd.DataFrame, list[pd.DataFrame]
        Data parsed from an .mpt/.mpr file or the data parsed from all
        techniques in an .mps file. Optionally also the parsed data is
        returned.

    """
    __, ext = os.path.splitext(path)
    if ext == '.mpt':
        mpt = parse_mpt(path)
        mpt_records = mpt['datapoints']
        df = pd.DataFrame.from_dict(mpt_records)
    elif ext == '.mpr':
        mpr = parse_mpr(path)
        mpr_records = mpr[1]['data']['datapoints']
        df = pd.DataFrame.from_dict(mpr_records)
    elif ext == '.mps':
        mps = parse_mps(path, load_data=True)
        df = []
        for technique in mps['techniques']:
            if 'data' not in technique:
                continue
            data = technique['data']
            # It's intentional to prefer .mpt over .mpr files here.
            if 'mpt' in data.keys():
                mpt_records = data['mpt']['datapoints']
                mpt_df = pd.DataFrame.from_dict(mpt_records)
                df.append(mpt_df)
            elif 'mpr' in data.keys():
                mpr_records = data['mpr'][1]['data']['datapoints']
                mpr_df = pd.DataFrame.from_dict(mpr_records)
                df.append(mpr_df)
    else:
        raise ValueError(f"Unrecognized file extension: {ext}")
    return df


def to_csv(path: str, csv_path: str = None) -> None:
    """Extracts the data from an .mpt/.mpr file or from the techniques
    in an .mps file and writes it to a number of .csv files.

    Parameters
    ----------
    path
        The path to the EC-Lab file to read in.
    csv_path
        Base path to use for the .csv files. The function automatically
        appends the technique number to the file name. Defaults to
        construct the .csv filename from the mpt_path.

    """
    df = to_df(path)
    if isinstance(df, pd.DataFrame):
        if csv_path is None:
            csv_path = _construct_path(path, '.csv')
        df.to_csv(csv_path, float_format='%.15f', index=False)
    elif isinstance(df, list):
        for i, df in enumerate(df):
            if csv_path:
                df.to_csv(
                    _construct_path(csv_path, f'_{i+1:02d}.csv'),
                    float_format='%.15f', index=False)
            df.to_csv(
                _construct_path(path, f'_{i+1:02d}.csv'),
                float_format='%.15f', index=False)


def to_xlsx(path: str, xlsx_path: str = None) -> None:
    """Extracts the data from an .mpt/.mpr file or from the techniques in
    an .mps file and writes it to an Excel file.

    Parameters
    ----------
    path
        The path to the EC-Lab file to read in.
    excel_path (optional)
        Path to the Excel file to write. Defaults to construct the
        filename from the mpt_path.

    """
    df = to_df(path)
    if xlsx_path is None:
        xlsx_path = _construct_path(path, '.xlsx')
    if isinstance(df, pd.DataFrame):
        df.to_excel(xlsx_path, index=False)
    elif isinstance(df, list):
        # pylint: disable=abstract-class-instantiated
        with pd.ExcelWriter(xlsx_path) as writer:
            for i, df in enumerate(df):
                df.to_excel(
                    writer, sheet_name=f'{i+1:02d}', index=False)


def _parse_arguments() -> argparse.Namespace:
    """Parses the arguments if invoked from the command line."""
    parser = argparse.ArgumentParser(
        description=(
            "Process the given file and write it in the specified file format"))
    parser.add_argument("file", type=str, help="the file to read")
    parser.add_argument("format", type=str, choices=['csv', 'xlsx'],
        default='csv', help="type of file to write")
    args = parser.parse_args()
    return args


def _run():
    args = _parse_arguments()
    if args.format == 'csv':
        to_csv(args.file)
    elif args.format == 'xlsx':
        to_xlsx(args.file)


if __name__ == '__main__':
    _run()
