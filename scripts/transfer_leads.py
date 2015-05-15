#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
from closeio_api import Client as CloseIO_API


def empty_if_none(val):
    return val if val is not None else ''

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="""
Transfering leads from one organization to another.

""")
parser.add_argument('--api-key', '-k', required=True, help='API Key')
parser.add_argument('--target-api-key', required=True, help='Target company API Key')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')
parser.add_argument('--delete', action='store_true',
                    help='Delete transfered leads.')
parser.add_argument('--confirmed', '-c', action='store_true',
                    help='Without this flag, the script will do a dry run without actually updating any data.')
parser.add_argument('query', help='Search query')

args = parser.parse_args()
log_format = "[%(asctime)s] %(levelname)s %(message)s"
if not args.confirmed:
    log_format = 'DRY RUN: '+log_format
logging.basicConfig(level=logging.INFO, format=log_format)
logging.debug('parameters: %s' % vars(args))

api = CloseIO_API(args.api_key, development=args.development)
target_api = CloseIO_API(args.target_api_key, development=args.development)

has_more = True
offset = 0

leads_to_transfer = []

if not 'sort:created' in args.query:
    lead_query = args.query + ' sort:created'
else:
    lead_query = args.query

while has_more:
    # Get a page of leads
    resp = api.get('lead', data={
        'query': lead_query,
        '_skip': offset,
    })
    leads = resp['data']

    for lead in leads:
        leads_to_transfer.append(lead)

    offset += max(0, len(leads) - 1)
    has_more = resp['has_more']

# statuses
status_map = {}
statuses_ids = set([x['status_id'] for x in leads_to_transfer])
for status_id in statuses_ids:
    status = api.get('status/lead/'+status_id)
    status_map[status['id']] = status['label']

# custom fields
resp = api.get('custom_fields/lead')
source_custom_fieldnames = [x['name'] for x in resp['data']]
resp = target_api.get('custom_fields/lead')
target_custom_fieldnames = [x['name'] for x in resp['data']]

new_custom_fieldnames = [x for x in source_custom_fieldnames if x not in target_custom_fieldnames]
for field in new_custom_fieldnames:
    target_api.post('custom_fields/lead', data={'name': field, 'type': 'text'})
    logging.info('added new custom field "%s"' % field)

for lead in leads_to_transfer:
    payload = {
        'name': empty_if_none(lead['name']),
        'url': empty_if_none(lead['url']),
        'description': empty_if_none(lead['description']),
        'status': status_map[lead['status_id']],
        'addresses': lead['addresses'],
        'custom': lead['custom'],
        'date_created': lead['date_created'],
        'date_updated': lead['date_updated']
    }

    new_contacts = []
    for contact in lead['contacts']:
        new_contacts.append({
            'name': contact['name'],
            'title': contact['title'],
            'phones': [{'phone': x['phone'], 'type': x['type']} for x in contact['phones']],
            'emails': [{'email': x['email'], 'type': x['type']} for x in contact['emails']],
            'urls': [{'url': x['url'], 'type': x['type']} for x in contact['urls']],
            'date_created': contact['date_created'],
            'date_updated': contact['date_updated']
        })
    payload['contacts'] = new_contacts

    if args.confirmed:
        new_lead = target_api.post('lead', data=payload)
    else:
        new_lead['id'] = None
        new_lead['name'] = lead['name']
    logging.info('target: * added %s %s' % (new_lead['id'], new_lead['name']))

    new_opportunities = []
    for oppo in lead['opportunities']:
        contact_ids = [x['id'] for x in new_lead['contacts'] if x['name'] == oppo['contact_name']]
        contact_id = None
        if contact_ids:
            contact_id = contact_ids[0]

        new_opportunities.append({
            'lead_id': new_lead['id'],
            'status': oppo['status_label'],
            'value': oppo['value'],
            'date_won': oppo['date_won'],
            'date_lost': oppo['date_lost'],
            'note': oppo['note'],
            'value_period': oppo['value_period'],
            'confidence': oppo['confidence'],
            'contact_id': contact_id,
            'date_created': oppo['date_created'],
            'date_updated': oppo['date_updated']

        })

    for payload in new_opportunities:
        if args.confirmed:
            new_oppo = target_api.post('opportunity', data=payload)
        else:
            new_oppo['id'] = None
        logging.info('target: %s added opportunity %s ' % (new_lead['id'], new_oppo['id']))

    # tasks
    new_tasks = []
    for task in lead['tasks']:
        new_tasks.append({
            'lead_id': new_lead['id'],
            'text': task['text'],
            'due_date': task['due_date'],
            'is_complete': task['is_complete'],
            'assigned_to': task['assigned_to']
        })

    for payload in new_tasks:
        if args.confirmed:
            new_task = target_api.post('task', data=payload)
        logging.info('target: %s added task: %s' % (new_lead['id'], payload['text']))
    has_more = True
    offset = 0

    # activity
    new_lead_activities = []
    while has_more:
        resp = api.get('activity', data={
            'lead_id': lead['id'],
            '_skip': offset,
        })

        activities = resp['data']

        for activity in activities:
            new_lead_activities.append(activity)

        offset += max(0, len(activities) - 1)
        has_more = resp['has_more']

    for activity in new_lead_activities:
        if activity['_type'] == 'Note':
            if args.confirmed:
                target_api.post('activity/note', data={
                    'lead_id': new_lead['id'],
                    'note': activity['note'],
                    'date_created': activity['date_created'],
                    'date_updated': activity['date_updated']
                })
            logging.info('target: %s added note: %s' % (new_lead['id'], activity['note']))

        elif activity['_type'] == 'Email':
            if args.confirmed:
                target_api.post('activity/email', data={
                    'lead_id': new_lead['id'],
                    'status': 'sent',
                    'direction': activity['direction'],
                    'attachments': activity['attachments'],
                    'subject': activity['subject'],
                    'body_text': activity['body_text'],
                    'body_html': activity['body_html'],
                    'sender': activity['sender'],
                    'to': activity['to'],
                    'cc': activity['cc'],
                    'bcc': activity['bcc'],
                    'envelope': activity['envelope'],
                    'date_created': activity['date_created'],
                    'date_updated': activity['date_updated']
                })
            logging.info('target: %s added email: %s %s' % (new_lead['id'], activity['to'], activity['subject']))
        elif activity['_type'] == 'Call':
            if args.confirmed:
                target_api.post('activity/call', data={
                    'lead_id': new_lead['id'],
                    'created_by_name': activity['created_by_name'],
                    'direction': activity['direction'],
                    'duration': activity['duration'],
                    'updated_by_name': activity['updated_by_name'],
                    'voicemail_duration': activity['voicemail_duration'],
                    'note': activity['note'],
                    'source': activity['source'],
                    'status': activity['status'],
                    'remote_phone': activity['remote_phone'],
                    'phone': activity['phone'],
                    'local_phone': activity['local_phone'],
                    'transferred_from': activity['transferred_from'],
                    'transferred_to': activity['transferred_to'],
                    'recording_url': activity['recording_url'],
                    'date_created': activity['date_created'],
                    'date_updated': activity['date_updated']
                })
            logging.info('target: %s added call: %s  duration: %s' % (new_lead['id'],
                                                                      activity['phone'],
                                                                      activity['duration']))
    if args.delete:
        api.put('lead/' + lead['id'])
        logging.info('deleted source lead %s' % (lead['id'],))


