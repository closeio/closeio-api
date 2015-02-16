import argparse
import logging
from closeio_api import Client as CloseIO_API

LEADS_QUERY = '* sort:created'

parser = argparse.ArgumentParser(description='changing old country code to new country code')
parser.add_argument('old_code', type=str, help='Old country code')
parser.add_argument('new_code', type=str, help='New country code')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')
parser.add_argument('--confirmed', '-c', action='store_true',
                    help='Without this flag, the script will do a dry run without actually updating any data.')
args = parser.parse_args()

log_format = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
if not args.confirmed:
    log_format = 'DRY RUN: '+log_format
logging.basicConfig(level=logging.DEBUG, format=log_format)
logging.debug('parameters: %s' % vars(args))

api = CloseIO_API(args.api_key, development=args.development)
has_more = True
offset = 0

while has_more:
    resp = api.get('lead', data={
        'query': LEADS_QUERY,
        '_skip': offset,
        '_fields': 'id,addresses'
    })

    leads = resp['data']

    for lead in leads:
        need_update = False
        for address in lead['addresses']:
            if address['country'] == args.old_code:
                address['country'] = args.new_code
                need_update = True
        if need_update:
            if args.confirmed:
                api.put('lead/'+lead['id'], data=lead)
            logging.info('updated lead: %s' % lead)

    offset += max(0, len(leads) - 1)
    has_more = resp['has_more']