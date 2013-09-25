#!/usr/bin/env python
import argparse
from client.api import CloseIO_API

DELETE_FIELDS = ['Field1', 'Field2', 'Field3']

parser = argparse.ArgumentParser(description='Delete the fields: ' + ', '.join(DELETE_FIELDS))
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--development', action='store_true', help='Use a development server rather than production.')
args = parser.parse_args()

api = CloseIO_API(args.api_key, development=args.development)

skip = 0
has_more = True

while has_more:
    resp = api.get('lead', data={'_skip': skip})
    leads = resp['data']

    for lead in leads:
        n_fields_deleted = 0
        custom = lead['custom'].copy()

        for field in DELETE_FIELDS:
            if custom.get(field):
                del custom[field]
                n_fields_deleted += 1

        if n_fields_deleted:
            print "LEAD: %s" % lead['id']
            print "\tBEFORE", lead['custom']
            print "\tAFTER", custom
            print
            api.put('lead/' + lead['id'], data={'custom': custom})

    skip += len(leads)
    has_more = resp['has_more']
