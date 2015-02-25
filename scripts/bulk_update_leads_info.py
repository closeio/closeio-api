#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import argparse
import csv
import logging
from closeio_api import Client as CloseIO_API, APIError

OPPORTUNITY_FIELDS = ['opportunity%s_note',
                      'opportunity%s_value',
                      'opportunity%s_value_period',
                      'opportunity%s_confidence',
                      'opportunity%s_status']


def get_contact_info(contact_no, csv_row, what, contact_type):
    columns = [x for x in csv_row.keys()
               if re.match(r'contact%s_%s[0-9]' % (contact_no, what), x) and csv_row[x]]
    contact_info = []
    for col in columns:
        contact_info.append({what: csv_row[col], 'type': contact_type})
    return contact_info

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="""
Imports leads and related data from a csv file with header.
Header's columns may be declared in any order. Detects csv dialect (delimeter and quotechar).
""", epilog="""
key columns:
    * lead_id                           - If exists and not empty, update using lead_id.
    * company                           - If lead_id is empty or is not exists, imports to
                                          first lead from found company. If the company was
                                          not found, loads as new lead.
lead columns:
    * url                               - lead url
    * description                       - lead description
    * status                            - lead status
    * note[0-9]                         - lead notes

opportunity columns (new items will be added if all values filled):
    * opportunity[0-9]_note             - opportunity note
    * opportunity[0-9]_value            - opportunity value in cents
    * opportunity[0-9]_value_period     - will have a value like one_time or monthly
    * opportunity[0-9]_confidence       - opportunity confidence
    * opportunity[0-9]_status           - opportunity status

contact columns (new contacts wil be added):
    * contact[0-9]_name                 - contact name
    * contact[0-9]_title                - contact title
    * contact[0-9]_phone[0-9]           - contact phones
    * contact[0-9]_email[0-9]           - contact emails
    * contact[0-9]_url[0-9]             - contact urls
""")

parser.add_argument('csvfile', type=argparse.FileType('rU'), help='csv file')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')
parser.add_argument('--confirmed', '-c', action='store_true',
                    help='Without this flag, the script will do a dry run without actually updating any data.')
parser.add_argument('--create-custom-fields', '-f', action='store_true',
                    help='Create new custom fields, if not exists.')
parser.add_argument('--disable-create', '-e', action='store_true',
                    help='Prevent new lead creation. Update only exists leads.')
parser.add_argument('--continue-on-error', '-s', action='store_true',
                    help='Do not abort import after first error')
args = parser.parse_args()

log_format = "[%(asctime)s] %(levelname)s %(message)s"
if not args.confirmed:
    log_format = 'DRY RUN: '+log_format
logging.basicConfig(level=logging.INFO, format=log_format)
logging.debug('parameters: %s' % vars(args))

sniffer = csv.Sniffer()
dialect = sniffer.sniff(args.csvfile.read(1024))
args.csvfile.seek(0)
c = csv.DictReader(args.csvfile, dialect=dialect)
assert any(x in ('company', 'lead_id') for x in c.fieldnames), \
    'ERROR: column "company" or "lead_id" is not found'


api = CloseIO_API(args.api_key, development=args.development)

resp = api.get('custom_fields/lead')
available_custom_fieldnames = [x['name'] for x in resp['data']]
new_custom_fieldnames = [x for x in [y.split('.')[1] for y in c.fieldnames if y.startswith('custom.')]
                         if x not in available_custom_fieldnames]

if new_custom_fieldnames:
    if args.create_custom_fields:
        for field in new_custom_fieldnames:
            if args.confirmed:
                api.post('custom_fields/lead', data={'name': field, 'type': 'text'})
            available_custom_fieldnames.append(field)
            logging.info('added new custom field "%s"' % field)
    else:
        logging.error('unknown custom fieldnames: %s' % new_custom_fieldnames)
        sys.exit(1)

logging.debug('avaliable custom fields: %s' % available_custom_fieldnames)

updated_leads = 0
new_leads = 0
skipped_leads = 0

for r in c:
    payload = {}

    if r.get('company'):
        payload['name'] = r['company']

    if r.get('url'):
        payload['url'] = r['url']

    if r.get('description'):
        payload['description'] = r['description']

    if r.get('status'):
        payload['status'] = r['status']

    contact_ids = [y[7] for y in r.keys() if re.match(r'contact[0-9]_name', y)]
    contacts = []
    for x in contact_ids:
        contact = {}
        if r.get('contact%s_name' % x):
            contact['name'] = r['contact%s_name' % x]
        if r.get('contact%s_title' % x):
            contact['title'] = r['contact%s_title' % x]
        phones = get_contact_info(x, r, 'phone', 'office')
        if phones:
            contact['phones'] = phones
        emails = get_contact_info(x, r, 'email', 'office')
        if emails:
            contact['emails'] = emails
        urls = get_contact_info(x, r, 'url', 'url')
        if urls:
            contact['urls'] = urls
        if contact:
            contacts.append(contact)
    if contacts:
        payload['contacts'] = contacts

    custom = {x.split('.')[1]: r[x] for x in r.keys() if x.startswith('custom.')
              and x.split('.')[1] in available_custom_fieldnames and r[x]}
    if custom:
        payload['custom'] = custom

    try:
        lead = None
        if r.get('lead_id') is not None:
            # exists lead
            resp = api.get('lead/%s' % r['lead_id'], data={
                'fields': 'id'
            })
            logging.debug('received: %s' % resp)
            lead = resp
        else:
            # first lead in the company
            resp = api.get('lead', data={
                'query': 'company:"%s" sort:created' % r['company'],
                '_fields': 'id,display_name,name,contacts,custom',
                'limit': 1
            })
            logging.debug('received: %s' % resp)
            if resp['total_results']:
                lead = resp['data'][0]

        if lead:
            logging.debug('to sent: %s' % payload)
            if args.confirmed:
                api.put('lead/' + lead['id'], data=payload)
            logging.info('line %d updated: %s %s' % (c.line_num,
                                                     lead['id'],
                                                     lead.get('name') if lead.get('name') else ''))
            updated_leads += 1
        # new lead
        elif lead is None and not args.disable_create:
            logging.debug('to sent: %s' % payload)
            if args.confirmed:
                lead = api.post('lead', data=payload)
            logging.info('line %d new: %s %s' % (c.line_num,
                                                 lead['id'] if args.confirmed else 'X',
                                                 payload['name']))
            new_leads += 1

        notes = [r[x] for x in r.keys() if re.match(r'note[0-9]', x) and r[x]]
        for note in notes:
            if args.confirmed:
                resp = api.post('activity/note', data={'note': note, 'lead_id': lead['id']})
            logging.debug('%s new note: %s' % (lead['id'], note))

        opportunity_ids = [x[11] for x in c.fieldnames if re.match(r'opportunity[0-9]_note', x)]
        for i in opportunity_ids:
            if all([r[x % i] for x in OPPORTUNITY_FIELDS]):
                if r['opportunity%s_value_period' % i] not in ('one_time', 'monthly'):
                    logging.error('line %d invalid value_period "%s" for lead %d' %
                                  (c.line_num, r['opportunity%s_value_period' % i], i)
                    )
                    continue
                api.post('opportunity', data={'lead_id': lead['id'],
                                              'note': r['opportunity%s_note' % i],
                                              'value_period': r['opportunity%s_value_period' % i],
                                              'confidence': r['opportunity%s_confidence' % i],
                                              'status': r['opportunity%s_status' % i]})
            else:
                logging.error('line %d is not a fully filled opportunity %s, skipped', (c.line_num, i))

    except APIError as e:
        logging.error('line %d skipped with error %s payload: %s' % (c.line_num, e, payload))
        skipped_leads += 1
        if not args.continue_on_error:
            logging.info('stopped on error')
            sys.exit(1)

logging.info('summary: updated[%d], new[%d], skipped[%d]' % (updated_leads, new_leads, skipped_leads))
if skipped_leads:
    sys.exit(1)

