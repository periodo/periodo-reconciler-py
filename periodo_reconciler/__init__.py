import csv
import requests
import io
import json
import uuid
from collections import OrderedDict
import urllib.parse

__all__ = ['RProperty', 'RQuery', 'PeriodoReconciler', 'CsvReconciler', 'non_none_values']

# a wrapper for https://github.com/periodo/periodo-reconciler/blob/master/API.md


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

    def reconcile(self, queries, method='GET'):
        queries_dict = OrderedDict([q.to_key_value() for q in queries])

        if method.upper() == 'GET':
            r = requests.get(self.base_url, params={
                             'queries': json.dumps(queries_dict)})
            if r.status_code == 200:
                return r.json()
            else:
                r.raise_for_status()
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
    def __init__(self, csvfile, p_recon, query,
                 location=None, start=None, stop=None, 
                 ignored_queries='', page_size=1000):

        """
        """


        self.csvfile = csvfile
        self.p_recon = p_recon
        self.query = query
        self.location = location
        self.start = start
        self.stop = stop
        self.ignored_queries = ignored_queries
        self.page_size = page_size

 
        # if the query matches any entry in ignored_queries,
        # throw out the match
        # using csv.reader to parse ignored_queries because the parameter is a comma=delimited list

        c_reader = csv.reader(io.StringIO(self.ignored_queries))
        try:
            self.ignored_queries_set = set(next(c_reader))
        except:
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


    def results_with_rows(self):

        # bin the input rows into pages and then feed the pages to the reconciler
        # from the reconciler, yield each result

        for (i, page) in enumerate(grouper(self.reader, self.page_size)):
            queries = []

            # TO DO: I might be unnecessarily reproducing the page in memory
            page_dict = OrderedDict()

            for (j, row) in enumerate(page):
                label = str(j)
                page_dict[label] = row

                queries.append(RQuery(
                    row[self.query],
                    label=label,
                    properties=[
                        RProperty(p, row[v]) for (p, v)
                        in self.included_properties.items()
                    ]
                ))

            responses = self.p_recon.reconcile(queries, method='post')

            for (label, row) in page_dict.items():
                print ('\r results_with_rows', i, label, end="")
                yield(row, responses[label])

    def matches(self, results_with_rows=None):
        """
        this method process the results to return only matches
        """

        # assume that the new match_* names are not already field names
        assert len(set(self.reader.fieldnames) &
                   set(['match_num', 'match_name', 'match_id'])) == 0

        # return matches from the entire CSV if
        # we're not processing the inputted subset of results
        if results_with_rows is None:
            results_with_rows = self.results_with_rows()


        for (row, response) in results_with_rows:
            results = response['result']
            matching_results = [
                result for result in results if result['match']]
            num_matches = len(matching_results)

            # I think that number of matches must be 0 or 1
            # otherwise: a bug in the reconciler
            assert num_matches < 2

            if num_matches == 1:
                match_name = results[0]['name']
                match_id = results[0]['id']
            else:
                match_name = ''
                match_id = ''

            row['match_num'] = num_matches
            row['match_name'] = match_name
            row['match_id'] = match_id

            # eliminate results in which the query is ignored_queries,

            if row[self.query] in self.ignored_queries_set:
                row['match_num'] = 0
                row['match_name'] = ''
                row['match_id'] = ''

            yield (row)

    def to_csv(self, csvfile, rows, fieldnames=None):
        if fieldnames is None:
            fieldnames = (self.reader.fieldnames +
                          ['match_num', 'match_name', 'match_id'])

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in rows:
            writer.writerow(row)
