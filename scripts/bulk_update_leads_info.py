import re
import argparse
import csv
import logging
from closeio_api import Client as CloseIO_API, APIError

get_contact_info = lambda key, row, what, typ: [{what: row[x], 'type': typ} for x in row.keys()
                                                if re.match(r'contact%s_%s[0-9]' % (key, what), x) and row[x]]

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('csvfile', type=argparse.FileType('rU'), help='csv file')
    parser.add_argument('--api_key', '-k', required=True, help='API Key')
    parser.add_argument('--development', '-d', action='store_true',
                        help='Use a development (testing) server rather than production.')
    parser.add_argument('--confirmed', '-c', action='store_true',
                        help='Without this flag, the script will do a dry run without actually updating any data.')
    parser.add_argument('--disable-create', '-x', action='store_true',
                        help='Prevent new lead creation. Update only exists leads.')
    args = parser.parse_args()
    logging.debug('parameters: %s' % vars(args))

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(args.csvfile.read(1024))
    args.csvfile.seek(0)
    c = csv.DictReader(args.csvfile, dialect=dialect)

    api = CloseIO_API(args.api_key, development=args.development)

    dry_run_prefix = 'DRY RUN:' if args.confirmed else ''

    for r in c:
        assert any(x in ('company', 'lead_id') for x in r.keys()), \
            'error: column company or lead_id not found at line %d' % (c.line_num,)

        payload = {'name': r['company'],
                   'url': r.get('url'),
                   'contacts': [{'name': r['contact%s_name' % x],
                                'title': r['contact%s_title' % x],
                                'phones': get_contact_info(x, r, 'phone', 'office'),
                                'emails': get_contact_info(x, r, 'email', 'office'),
                                'urls': get_contact_info(x, r, 'url', 'url')}
                                for x in [y[7] for y in r.keys()
                                          if re.match(r'contact[0-9]_name', y) and r[y]]],
                   }

        custom = {x.split('.')[1]: r[x] for x in [y for y in r.keys() if y.startswith('custom.')]}

        lead = None

        # exists lead
        if r.get('lead_id') is not None:
            try:
                resp = api.get('lead/%s' % r['lead_id'], data={
                    'fields': 'id,display_name,name,contacts,custom'
                })

                if resp['total_results'] and args.confirmed:
                    lead = resp['data']
                    pass # updating exists lead
                    logging.info('%s updated exists lead %s' % (dry_run_prefix, lead['id']))
                    continue
            except APIError as e:
                logging.error('%s %s : lead_id: %s' % (dry_run_prefix, e, r['lead_id']))

        # first lead in company
        if lead is None:
            try:
                resp = api.get('lead', data={
                    'query': 'company: %s sort:created' % r['company'],
                    '_fields': 'id,display_name,name,contacts,custom',
                    'limit': 1
                })
                if resp['total_results']:
                    lead = resp['data']
                    print lead
                    continue
            except APIError as e:
                logging.error('%s %s : company: "%s"' % (dry_run_prefix, e, r['company']))

        # new lead
        if lead is None and not args.disable_create:
            try:
                resp = api.post('lead', data = payload)
            except APIError as e:
                logging.error('%s %s : payload: "%s"' % (dry_run_prefix, e, payload))
