#!/usr/bin/env python
# -*- coding: utf-8 -*-


def all(api, query='*'):
    has_more = True

    while has_more:
        resp = api.get('lead', data={
            'query': query,
            '_fields': 'id,addresses'
        })

        leads = resp['data']

        for lead in leads:
            yield lead

        has_more = resp['has_more']
