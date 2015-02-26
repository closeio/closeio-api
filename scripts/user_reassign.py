#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging

from closeio_api import Client as CloseIO_API, APIError

parser = argparse.ArgumentParser(description='Assigns tasks or opportunities from one user to another')
group_from = parser.add_mutually_exclusive_group(required=True)
group_from.add_argument('--from-user-id', '-f', type=str, help='')
group_from.add_argument('--from-user-email', type=str, help='')
group_to = parser.add_mutually_exclusive_group(required=True)
group_to.add_argument('--to-user-id', '-t', type=str, help='')
group_to.add_argument('--to-user-email', type=str, help='')

parser.add_argument('--api-key', '-k', required=True, help='')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')
parser.add_argument('--confirmed', '-c', action='store_true',
                    help='Without this flag, the script will do a dry run without actually updating any data.')
parser.add_argument('--continue-on-error', '-s', action='store_true', help='Do not abort after first error')
group = parser.add_argument_group()
group.add_argument('--tasks', '-T', action='store_true', help='reassign only non complete tasks')
group.add_argument('--all-tasks', action='store_true', help='reassign all tasks')
group.add_argument('--opportunities', '-O', action='store_true', help='reassign only active opportunities')
group.add_argument('--all-opportunities', action='store_true', help='reassign all opportunities')


args = parser.parse_args()

if not any([args.tasks, args.opportunities, args.all_tasks, args.all_opportunities]):
    parser.error("at least one option required")

log_format = "[%(asctime)s] %(levelname)s %(message)s"
if not args.confirmed:
    log_format = 'DRY RUN: '+log_format
logging.basicConfig(level=logging.INFO, format=log_format)
logging.debug('parameters: %s' % vars(args))

api = CloseIO_API(args.api_key, development=args.development)

emails_to_ids = {}
if any([args.from_user_email, args.to_user_email]):
    has_more = True
    offset = 0
    while has_more:
        resp = api.get('user')
        for user in resp['data']:
            emails_to_ids[user['email']] = user['id']
        offset += max(0, len(resp['data']) - 1)
        has_more = resp['has_more']

logging.debug(emails_to_ids)

if args.from_user_email:
    from_user_id = emails_to_ids[args.from_user_email]
else:
    # for exception, if user_id is not present in the database
    resp = api.get('user/'+args.from_user_id, data={
        '_fields': 'id'
    })

    from_user_id = resp['id']

if args.to_user_email:
    to_user_id = emails_to_ids[args.to_user_email]

else:
    resp = api.get('user/'+args.to_user_id, data={
        '_fields': 'id'
    })

    to_user_id = resp['id']

ids_to_emails = dict((v, k) for k, v in emails_to_ids.iteritems())

logging.info('from user_id %s (%s)' % (from_user_id, ids_to_emails[from_user_id]))
logging.info('to user_id: %s (%s)' % (to_user_id, ids_to_emails[to_user_id]))

assert from_user_id != to_user_id, 'equal user codes'

opportunities_errors = 0
tasks_errors = 0
try:
    # tasks
    updated_tasks = 0
    if args.tasks or args.all_tasks:
        has_more = True
        offset = 0
        while has_more:
            payload = {
                'assigned_to': from_user_id,
                '_order_by': 'date_created',
                '_skip': offset,
                '_fields': 'id'
            }

            if not args.all_tasks:
                payload['is_complete'] = False

            resp = api.get('task', data=payload)

            tasks = resp['data']
            for task in tasks:
                if args.confirmed:
                    try:
                        api.put('task/'+task['id'], data={'assigned_to': to_user_id})
                    except APIError as e:
                        tasks_errors += 1
                        if not args.continue_on_error:
                            raise e
                        logging.error('task %s skipped with error %s' % (task['id'], e))
                logging.info('updated %s' % task['id'])
                updated_tasks += 1

            offset += max(0, len(tasks) - 1)
            has_more = resp['has_more']

    # opportunities
    updated_opportunities = 0
    if args.opportunities or args.all_opportunities:
        has_more = True
        offset = 0
        while has_more:
            payload = {
                'user_id': from_user_id,
                '_order_by': 'date_created',
                '_skip': offset,
                '_fields': 'id'
            }

            if not args.all_opportunities:
                payload['status_type'] = 'active'

            resp = api.get('opportunity', data=payload)

            opportunities = resp['data']
            for opportunity in opportunities:
                if args.confirmed:
                    try:
                        api.put('opportunity/'+opportunity['id'], data={'user_id': to_user_id})
                    except APIError as e:
                        opportunities_errors += 1
                        if not args.continue_on_error:
                            raise e
                        logging.error('opportunity %s skipped with error %s' % (opportunity['id'], e))
                logging.info('updated %s' % opportunity['id'])
                updated_opportunities += 1

            offset += max(0, len(opportunities) - 1)
            has_more = resp['has_more']
except APIError:
    logging.error('stopped on error %s' % e)

logging.info('summary: updated tasks %d, updated opportunities %d' % (updated_tasks, updated_opportunities))
if opportunities_errors or tasks_errors:
    logging.info('summary: tasks errors: %s, opportunities errors %d' % (tasks_errors, opportunities_errors))
