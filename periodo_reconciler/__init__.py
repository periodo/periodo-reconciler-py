import csv
import requests
import io
import json
import uuid
from collections import OrderedDict, defaultdict, Counter
import urllib.parse
from functools import lru_cache

# for LRU cache
CACHE_MAX_SIZE = 65536

__all__ = ['RProperty', 'RQuery', 'PeriodoReconciler',
           'CsvReconciler', 'non_none_values', 'grouper', 'CACHE_MAX_SIZE']

# a wrapper for
# https://github.com/periodo/periodo-reconciler/blob/master/API.md


# http://stackoverflow.com/questions/2348317/how-to-write-a-pager-for-python-iterators/2350904#2350904
def grouper(iterator, page_size):
    """
    yield pages of results from input interable


    Parameters
    ----------
    iterator : Python interator
        the iterator to be converted into pages
    page_size : int
        page size

    Returns
    -------
    iterator
        a iterator of pages

    """
    page = []
    for item in iterator:
        page.append(item)
        if len(page) == page_size:
            yield page
            page = []
    if len(page) > 0:
        yield page


def non_none_values(dict_):
    return dict([
        (k, v) for (k, v) in dict_.items() if v is not None
    ])


class RProperty(object):
    def __init__(self, p, v):
        self.p = p
        self.v = v

    def to_dict(self):
        return {'p': self.p, 'v': self.v}

    def __repr__(self):
        return ("""RProperty({}, {})"""
                .format(json.dumps(self.p), json.dumps(self.v)))


class RQuery(object):
    def __init__(self, query, label=None, limit=None, properties=None):
        self.query = query
        if label is None:
            self.label = str(uuid.uuid4())
        else:
            self.label = label
        self.limit = limit
        self.properties = properties

    def to_key_value(self):
        v = {'query': self.query}
        if self.limit is not None:
            v['limit'] = self.limit
        if (self.properties is not None and len(self.properties)):
            v['properties'] = [p.to_dict() for p in self.properties]

        return (self.label, v)

    def __repr__(self):
        if (self.properties is not None) and (len(self.properties)):
            properties_repr = (""", properties=[{}]"""
                               .format(",\n".join([repr(p)
                                                   for p in self.properties])))
        else:
            properties_repr = ""

        if self.limit is not None:
            limit_repr = ", limit={}".format(json.dumps(self.limit))
        else:
            limit_repr = ""

        return ("""RQuery({}, label={}{}{})"""
                .format(json.dumps(self.query),
                        json.dumps(
                    self.label),
                    limit_repr,
                    properties_repr))


class PeriodoReconciler(object):
    def __init__(self, host='localhost:8142', protocol='http'):
        self.host = host
        self.protocol = protocol
        self.base_url = '{}://{}/'.format(protocol, host)

    def __repr__(self):
        return ("""PeriodoReconciler(host={}, protocol={})"""
                .format(json.dumps(self.host),
                        json.dumps(self.protocol)))

    def describe(self):
        r = requests.get(self.base_url)
        return r.json()

    @lru_cache(maxsize=CACHE_MAX_SIZE)
    def _call_reconciler(self, query_dict_json, method='GET'):
        if method.upper() == 'GET':
            r = requests.get(self.base_url, params={
                             'queries': query_dict_json})
        elif method.upper() == 'POST':
            r = requests.post(self.base_url, data={
                              'queries': query_dict_json})

        if r.status_code == 200:
            return r.json()
        else:
            r.raise_for_status()

    def _reconcile_query_by_query(self, queries, method='GET'):

        queries_dict = OrderedDict([q.to_key_value() for q in queries])
        results_dict = dict()

        for (k, v) in queries_dict.items():
            # don't let the label for the query mess up the caching
            query_dict = {'_': v}
            query_dict_json = json.dumps(query_dict, sort_keys=True)
            result = self._call_reconciler(query_dict_json, method)
            results_dict[k] = result['_']

        return results_dict

    def reconcile(self, queries, method='GET', query_by_query=False):

        if query_by_query:
            return self._reconcile_query_by_query(queries, method)

        queries_dict = OrderedDict([q.to_key_value() for q in queries])

        if method.upper() == 'GET':
            r = requests.get(self.base_url, params={
                             'queries': json.dumps(queries_dict)})
        elif method.upper() == 'POST':
            r = requests.post(self.base_url, data={
                              'queries': json.dumps(queries_dict)})

        if r.status_code == 200:
            return r.json()
        else:
            r.raise_for_status()

    def suggest_properties(self):
        r = requests.get(urllib.parse.urljoin(
            self.base_url, '/suggest/properties'))
        if r.status_code == 200:
            return r.json()['result']

    def suggest_entities(self, prefix):
        r = requests.get(urllib.parse.urljoin(
            self.base_url, '/suggest/entities'), params={
                'prefix': prefix
        })
        if r.status_code == 200:
            return r.json()['result']

    def preview_period(self, period_id, flyout=False):
        params = {'id': period_id}
        if flyout:
            params['flyout'] = True

        url = urllib.parse.urljoin(self.base_url, '/preview')
        r = requests.get(urllib.parse.urljoin(
            self.base_url, '/preview'), params=params)
        if r.status_code == 200:
            return r.content
        else:
            r.raise_for_status()


class CsvReconciler(object):

    match_column_fields = (
        'match_num', 'match_name', 'match_id',
        'candidates_count',
        'match_fallback_id', 'match_fallback_name')

    def __init__(self, csvfile, p_recon, query,
                 location=None, start=None, stop=None,
                 ignored_queries='',
                 transpose_query=False,
                 page_size=1000,
                 query_by_query=True,
                 match_column_prefix="",
                 match_top_candidate=True):
        """
        """

        self.csvfile = csvfile
        self.p_recon = p_recon
        self.query = query
        self.location = location
        self.start = start
        self.stop = stop
        self.ignored_queries = ignored_queries
        self.transpose_query = transpose_query
        self.page_size = page_size
        self.query_by_query = query_by_query
        self.match_column_prefix = match_column_prefix
        self.match_top_candidate = match_top_candidate

        # if the query matches any entry in ignored_queries,
        # throw out the match
        # using csv.reader to parse ignored_queries because the parameter is
        # a comma=delimited list

        c_reader = csv.reader(io.StringIO(self.ignored_queries))
        try:
            self.ignored_queries_set = set(next(c_reader))
        except StopIteration as e:
            self.ignored_queries_set = set()

        self.reader = csv.DictReader(csvfile)

        # check that query, location, start, stop are in fieldnames
        # TO DO: I may want to move away from using assert
        for f in [query, location, start, stop]:
            if f is not None:
                assert f in self.reader.fieldnames

        # which properties are included?
        self.included_properties = non_none_values({
            'location': location,
            'start': start,
            'stop': stop
        })

        # compute the columns names for the match results, which
        # have an optional prefix (match_column_prefix)

        self.match_column_names = OrderedDict(
            [(name, f"{self.match_column_prefix}{name}")
             for name in CsvReconciler.match_column_fields])

        # initialize a summary count of the matches
        self.match_summary = Counter()

    def _transpose_query(self, q):
        """
        transpose only if there is a single ","
        """
        if not self.transpose_query:
            return q

        terms = [term.strip() for term in q.split(",")]
        if (len(terms) == 2):
            return terms[1] + " " + terms[0]
        else:
            return q

    def results_with_rows(self):

        # bin the input rows into pages and then feed the pages
        # to the reconciler
        # from the reconciler, yield each result

        for (i, page) in enumerate(grouper(self.reader, self.page_size)):
            queries = []

            # TO DO: I might be unnecessarily reproducing the page in memory
            page_dict = OrderedDict()

            for (j, row) in enumerate(page):
                label = str(j)
                page_dict[label] = row

                queries.append(RQuery(
                    self._transpose_query(row[self.query]),
                    label=label,
                    properties=[
                        RProperty(p, row[v]) for (p, v)
                        in self.included_properties.items()
                    ]
                ))

            responses = self.p_recon.reconcile(
                queries,
                method='post',
                query_by_query=self.query_by_query)

            for (label, row) in page_dict.items():
                # print ('\r results_with_rows', i, label, end="")
                yield(row, responses[label])

    def _matches(self, results_with_rows=None):
        """
        this method process the results to return only matches
        """

        # assume that the new match_* names are not already field names
        assert len(set(self.reader.fieldnames) &
                   set(self.match_column_names.values())) == 0

        # return matches from the entire CSV if
        # we're not processing the inputted subset of results
        if results_with_rows is None:
            results_with_rows = self.results_with_rows()

        # compute a counter on the matches in the loop
        # mapping query to match_id, match_name
        self.matches_for_query = defaultdict(Counter)

        for (row, response) in results_with_rows:
            results = response['result']
            matching_results = [
                result for result in results if result['match']]
            match_num = len(matching_results)

            # I think that number of matches must be 0 or 1
            # otherwise: a bug in the reconciler
            assert match_num < 2

            if (match_num == 1) or (self.match_top_candidate and len(results)):
                match_name = results[0]['name']
                match_id = results[0]['id']

                # keep track of how many times a given query
                # maps to a (match_id, match_name) tuple
                (self.matches_for_query[row[self.query]]
                    .update([(match_id, match_name)]))

            else:
                match_name = ''
                match_id = ''

            row[self.match_column_names['candidates_count']] = len(results)

            row[self.match_column_names["match_num"]] = match_num
            row[self.match_column_names["match_name"]] = match_name
            row[self.match_column_names["match_id"]] = match_id
            row[self.match_column_names["match_fallback_id"]] = ''
            row[self.match_column_names["match_fallback_name"]] = ''

            # eliminate results in which the query is in ignored_queries

            if row[self.query] in self.ignored_queries_set:
                row[self.match_column_names["match_num"]] = 0
                row[self.match_column_names["match_name"]] = ''
                row[self.match_column_names["match_id"]] = ''

            yield (row)

    def matches(self, results_with_rows=None):
        """
        _matches is the first pass
        """

        rows = list(self._matches(results_with_rows))
        self.match_summary = Counter()

        # let's now calculate fallback for rows
        # without matches
        for row in rows:
            if not row[self.match_column_names["match_id"]]:
                # set as fallback as the most common match
                # for the same query term
                query = row[self.query]
                c = self.matches_for_query[query].most_common(1)
                if len(c):
                    ((match_id, match_name), count) = c[0]
                    row[(self
                         .match_column_names["match_fallback_id"])] = match_id
                    row[(self
                         .match_column_names
                         ["match_fallback_name"])] = match_name

            self.match_summary.update([(
                row[self.query],
                row[self.location] if self.location is not None else '',
                row[self.start] if self.start is not None else '',
                row[self.stop] if self.stop is not None else '',
                row[self.match_column_names["match_num"]],
                row[self.match_column_names["match_name"]],
                row[self.match_column_names["match_id"]],
                row[self.match_column_names["candidates_count"]],
                row[self.match_column_names["match_fallback_id"]],
                row[self.match_column_names["match_fallback_name"]]
            )])
            yield row

    def to_csv(self, csvfile, rows, fieldnames=None):
        if fieldnames is None:
            fieldnames = (
                self.reader.fieldnames +
                list(self.match_column_names.values())
            )

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    def match_summary_to_csv(self, output):
        """
        return self.self.match_summary as CSV
        """

        headers = (['query', 'location', 'start', 'stop'] +
                   list(CsvReconciler.match_column_fields) + ['row_count'])

        writer = csv.DictWriter(output, fieldnames=headers)

        writer.writeheader()
        for (v, c) in self.match_summary.most_common():
            row = OrderedDict(zip(headers, list(v) + [c]))
            writer.writerow(row)
