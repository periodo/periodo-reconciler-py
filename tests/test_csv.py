import json
import csv
import os
import pytest
from periodo_reconciler import (
    RProperty,
    RQuery,
    PeriodoReconciler,
    CsvReconciler
)
from collections import OrderedDict

from .fixtures import p_recon


def output_path_name(inpath):

    (basename, fext) = os.path.splitext(inpath)

    return basename + '-recon' + fext
    return output_fname


def test_simple_csv(p_recon):

    csv_path = "test-data/periodo_simple_example.csv"
    csvfile = open(csv_path)
    c_recon = CsvReconciler(csvfile, p_recon, 'query',
                            'location', 'start', 'end')
    r = list(c_recon.matches())
    assert len(r) == 5


def test_to_csv(p_recon):
    import contextlib

    csv_path = "test-data/periodo_simple_example.csv"
    output_path = output_path_name(csv_path) + ".temp"

    # https://stackoverflow.com/a/19412700/7782
    with contextlib.ExitStack() as stack:

        if os.path.exists(output_path):
            os.remove(output_path)

        csvfile = stack.enter_context(open(csv_path))
        outputfile = stack.enter_context(open(output_path, "w"))

        p_recon = PeriodoReconciler(host='localhost:8142')
        c_recon = CsvReconciler(csvfile, p_recon, 'query',
                                'location', 'start', 'end')
        c_recon.to_csv(outputfile, c_recon.matches())

    with open(output_path) as f:
        reader = csv.DictReader(f)
        assert 'match_id' in reader.fieldnames

    os.remove(output_path)


def test_ignored_queries(p_recon):

    # ignore the query == "bronze age"

    csv_path = "test-data/periodo_simple_example.csv"
    csvfile = open(csv_path)
    c_recon = CsvReconciler(csvfile, p_recon, 'query',
                            'location', 'start', 'end',
                            ignored_queries='bronze age')
    rows = list(c_recon.matches())
    for row in rows:
        if row['query'] == 'bronze age':
            assert row['match_num'] == 0


def test_transpose_query(p_recon):

    # compare the effects of running transpose_query
    # option True or False with each other

    csv_path = "test-data/periodo_simple_example.csv"
    csvfile = open(csv_path)
    c_recon = CsvReconciler(csvfile, p_recon, 'query',
                            'location', 'start', 'end',
                            transpose_query=True)

    rows = OrderedDict([(row['query'], row) for row in c_recon.matches()])

    # show that the row which has "Late Roman" matches "Roman, Late"
    assert rows['Late Roman']['match_id'] == rows['Roman, Late']['match_id']

    # show that if we don't tranpose_query, Roman, Late and Late Roman don't
    # match

    csvfile = open(csv_path)
    c_recon = CsvReconciler(csvfile, p_recon, 'query',
                            'location', 'start', 'end',
                            transpose_query=False)

    rows = OrderedDict([(row['query'], row) for row in c_recon.matches()])
    assert rows['Late Roman']['match_id'] != rows['Roman, Late']['match_id']
