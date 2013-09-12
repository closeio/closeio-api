#!/usr/bin/env python
import argparse
from flask_common.utils import CsvWriter
from client.api import CloseIO_API

HEADERS = ['lead_name', 'status_type', 'status_label', 'confidence', 'user_name', 'value', 'value_period', 'note', 'date_created', 'date_updated', 'date_won']

parser = argparse.ArgumentParser(description='Export Opportunities to CSV')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--output', '-o', required=True, help='Output filename')
parser.add_argument('--development', action='store_true', help='Use a development server rather than production.')
args = parser.parse_args()

with open(args.output, 'wb') as f:
    writer = CsvWriter(f)
    api = CloseIO_API(args.api_key, development=args.development)

    writer.writerow(HEADERS)

    skip = 0
    has_more = True

    while has_more:
        resp = api.get('opportunity', data={'_skip': skip})
        opportunities = resp['data']

        for opportunity in opportunities:
            row = []
            for header in HEADERS:
                row.append(opportunity.get(header) or '')
            writer.writerow(row)

        skip += len(opportunities)
        has_more = resp['has_more']

