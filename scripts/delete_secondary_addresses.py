#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import time

from closeio_api import Client as CloseIO_API, APIError


def run(api_key, development, confirmed, limit=100):
    api = CloseIO_API(api_key, development=development)

    # loop through existing leads with multiple addresses

    LEADS_QUERY_WITH_MULTIPLE_ADDRESSES = "addresses > 1 sort:created"
    has_more = True

    while has_more:
        resp = api.get('lead', data={
            'query': LEADS_QUERY_WITH_MULTIPLE_ADDRESSES,
            '_fields': 'id,addresses',
            '_limit': limit,
        })

        leads = resp['data']

        for lead in leads:
            if len(lead['addresses']) < 2:
                logging.warning("unexpected result: %s", lead)
                continue # this shouldn't happen based on the search query, but just to be safe...
            if confirmed:
                api.put('lead/' + lead['id'], data={'addresses': lead['addresses'][:1]})
            logging.info("removed %d extra address(es) for %s\n%s" % (len(lead['addresses'][1:]), lead['id'], lead['addresses'][1:]))

        has_more = resp['has_more']

        time.sleep(2)  # give the search indexer some time to catch up with the changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete all but first address for leads with multiple addresses.')
    parser.add_argument('--api-key', '-k', required=True, help='')
    parser.add_argument('--confirmed', '-c', action='store_true',
                        help='Without this flag, the script will do a dry run without actually updating any data.')
    parser.add_argument('--development', '-d', action='store_true',
                        help='Use a development (testing) server rather than production.')
    args = parser.parse_args()

    log_format = "[%(asctime)s] %(levelname)s %(message)s"
    if not args.confirmed:
        log_format = 'DRY RUN: ' + log_format
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.debug('parameters: %s' % vars(args))

    run(api_key=args.api_key, development=args.development, confirmed=args.confirmed)
