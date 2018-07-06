import json
import pytest
from periodo_reconciler import (
    RProperty,
    RQuery,
    PeriodoReconciler
)

from .fixtures import p_recon


def test_describe(p_recon):
    assert set(p_recon.describe().keys()) == {'defaultTypes',
                                              'identifierSpace',
                                              'name',
                                              'preview',
                                              'schemaSpace',
                                              'suggest',
                                              'view'}


def test_documentation_query(p_recon):
    queries = [
        RQuery("北宋", label="basic-query"),
        RQuery("bronze age",
               label="limited-query",
               limit=1),
        RQuery("Ранньоримський",
               label="additional-properties-query",
               properties=[
                   RProperty('location', 'Ukraine'),
                   RProperty('start', 200),
                   RProperty('end', 600)
               ])
    ]

    r1 = p_recon.reconcile(queries, method='get')
    r2 = p_recon.reconcile(queries, method='post')

    assert r1 == {'additional-properties-query':
                  {'result':
                   [{
                    'id': 'http://n2t.net/ark:/99152/p06v8w4dbcf',
                    'match': True,
                    'name':
                    'Ранньоримський період [Ukraine, Ukraine: -0049 to 0175]',
                    'score': 0,
                    'type':
                    [{'id': 'http://www.w3.org/2004/02/skos/core#Concept',
                      'name': 'Period definition'}]}]},
                  'basic-query':
                  {'result':
                   [{
                       'id': 'http://n2t.net/ark:/99152/p0fp7wvjvn8',
                    'match': True,
                    'name': 'Northern Song [China, China: 0960 to 1127]',
                    'score': 0,
                    'type':
                    [{'id': 'http://www.w3.org/2004/02/skos/core#Concept',
                      'name': 'Period definition'}]}]},
                  'limited-query':
                  {'result':
                   [{
                       'id': 'http://n2t.net/ark:/99152/p0z3skmnss7',
                       'match': False,
                       'name':
                       'Bronze [Palestine, Israel, Jordan: -3299 to -1199]',
                       'score': 0,
                       'type':
                       [{'id': 'http://www.w3.org/2004/02/skos/core#Concept',
                         'name': 'Period definition'}]}]}}

    assert (r1 == r2)


def test_suggest_properties(p_recon):
    result = p_recon.suggest_properties()
    for row in result:
        assert(set(row.keys()) == {'id', 'name'})


def test_suggest_entities(p_recon):
    result = p_recon.suggest_entities('bashkekohore')

    assert result == [{
        'id': 'http://n2t.net/ark:/99152/p06v8w4nfqg',
        'name': 'Bashkëkohore [Albania, Albania: 1944 to 2000]',
        'type': [{'id': 'http://www.w3.org/2004/02/skos/core#Concept',
                  'name': 'Period definition'}], 'score': 0, 'match': False},
        {'id': 'http://n2t.net/ark:/99152/p0qhb662s6j',
         'name': 'Bashkëkohore [Albania, Albania: 1944 to 2000]',
         'type': [{'id': 'http://www.w3.org/2004/02/skos/core#Concept',
                   'name': 'Period definition'}], 'score': 0, 'match': False}]


def test_preview(p_recon):
    r = p_recon.preview_period('http://n2t.net/ark:/99152/p0fp7wvjvn8')
    assert (b'<!doctype html>' in r)


def test_preview_flyout(p_recon):
    r = p_recon.preview_period(
        'http://n2t.net/ark:/99152/p0fp7wvjvn8',  flyout=True)
    assert 'html' in json.loads(r.decode('utf-8')).keys()
