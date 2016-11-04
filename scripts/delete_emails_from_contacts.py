#!/usr/bin/env python

import argparse, json, sys
from requests.exceptions import ConnectionError
from closeio_api import APIError, Client as CloseIO_API
from closeio_api.utils import CsvReader

parser = argparse.ArgumentParser(description='Remove email addresses from contacts in CSV file')
parser.add_argument('--api-key', '-k', required=True, help='API Key')
parser.add_argument('--confirmed', action='store_true', help='Confirm making changes. Otherwise this script is not going to modify any data.')
parser.add_argument('--verbose', '-v', action='store_true', help='Increase logging verbosity.')
parser.add_argument('file', help='Path to the csv file')
args = parser.parse_args()

reader = CsvReader(args.file)

headers = dict([(name, idx,) for idx, name in enumerate(reader.next())]) # skip the 1st line header

if any(field not in headers for field in ['contact_id', 'email_address']):
    print 'contact_id or email_address headers could not be found in your csv file.'
    sys.exit(-1)

api = CloseIO_API(args.api_key, async=False)

for row in reader:
    contact_id = row[headers['contact_id']]
    email_address = row[headers['email_address']]

    if args.verbose:
        print 'Attempting to remove %s from %s' % (email_address, contact_id)

    try:
        contact = api.get('contact/' + contact_id)

        if not contact['emails']:
            if args.verbose:
                print 'Skipping %s because it has no email addresses' % contact_id)
            continue

        emails = filter(lambda email: email['email'] != email_address, contact['emails'])
        if args.confirmed:
            resp = api.put('contact/' + contact_id, {'emails': emails})
            if args.verbose:
                print 'Removed %s from %s' % (email_address, contact_id)
    except APIError as e:
        if args.verbose:
            print 'Encountered an API error (%s): %s' % (
                e.response.status_code,
                e.response.text
            )
