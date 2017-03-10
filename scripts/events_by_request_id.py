#!/usr/bin/env python

import logging
import sys
import json
import argparse
from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='Detect duplicates & merge leads (see source code for details)')
parser.add_argument('--api-key', required=True, help='API Key')
parser.add_argument('--request-id', required=True, help='request_id from event log.')
parser.add_argument('--date-gt', required=True, help='date_updated greater than.')
parser.add_argument('--date-lt', required=True, help='date_updated less than.')
parser.add_argument('--output', '-o', required=True, help='json output file of events')
parser.add_argument('--verbose', '-v', action='store_true', help='Increase logging verbosity.')
args = parser.parse_args()

api = CloseIO_API(args.api_key)


def setup_logger():
    logger = logging.getLogger('closeio.api.events_by_request_id')
    logger.setLevel(logging.INFO)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = setup_logger()

output = open(args.output,"w") 
output.write("[")

has_more = True
cursor = None
while has_more:
    resp = api.get('event', params={'date_updated__gt': args.date_gt, 'date_updated__lt': args.date_lt, '_cursor': cursor})
    for event in resp['data']:
        if event['request_id'] == args.request_id:
            json.dump(event, output, indent=4)
            output.write(",")
    cursor = resp['cursor_next']
    has_more = bool(cursor)
    print cursor

output.write("]")
output.close()
