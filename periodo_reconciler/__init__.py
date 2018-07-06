import requests
import json
import uuid
from collections import OrderedDict
import urllib.parse

__all__ = ['RProperty', 'RQuery', 'PeriodoReconciler']


class RProperty(object):
    def __init__(self, p, v):
        self.p = p
        self.v = v

    def to_dict(self):
        return {self.p: self.v}


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


class PeriodoReconciler(object):
    def __init__(self, host='localhost:8142', protocol='http'):
        self.host = host
        self.base_url = '{}://{}/'.format(protocol, host)

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
        print(url, params)
        r = requests.get(urllib.parse.urljoin(
            self.base_url, '/preview'), params=params)
        if r.status_code == 200:
            return r.content
        else:
            r.raise_for_status()
