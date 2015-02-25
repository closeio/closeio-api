#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging

from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='Assigns tasks or opportunities from one user to another')
parser.add_argument('--from-user-id', '-f', type=str, help='')
parser.add_argument('--to-user-id', '-t', type=str, help='')
parser.add_argument('--api-key', '-k', required=True, help='')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')
parser.add_argument('--confirmed', '-c', action='store_true',
                    help='Without this flag, the script will do a dry run without actually updating any data.')
group = parser.add_argument_group()
group.add_argument('--tasks', '-T', action='store_true',
                   help='')
group.add_argument('--all-tasks', action='store_true')
group.add_argument('--opportunities', '-O', action='store_true')
group.add_argument('--all-opportunities', action='store_true')


args = parser.parse_args()

if not any([args.tasks, args.opportunities, args.all_tasks, args.all_opportunities]):
    parser.error("at least one option required")

assert args.from_user_id != args.to_user_id, 'equal user codes'

log_format = "[%(asctime)s] %(levelname)s %(message)s"
if not args.confirmed:
    log_format = 'DRY RUN: '+log_format
logging.basicConfig(level=logging.INFO, format=log_format)
logging.debug('parameters: %s' % vars(args))

api = CloseIO_API(args.api_key, development=args.development)

# check users
from_user = api.get('user/'+args.from_user_id)
logging.debug(from_user)
to_user = api.get('user/'+args.to_user_id)
logging.debug(to_user)

# tasks
if args.tasks or args.all_tasks:
    has_more = True
    offset = 0
    while has_more:
        payload = {
            'assigned_to': args.from_user_id,
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
                api.put('task/'+task['id'], data={'assigned_to': args.to_user_id})
            logging.info('updated task %s' % task['id'])

        offset += max(0, len(tasks) - 1)
        has_more = resp['has_more']

# opportunities
if args.opportunities or args.all_opportunities:
    has_more = True
    offset = 0
    while has_more:
        payload = {
            'user_id': args.from_user_id,
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
                api.put('opportunity/'+opportunity['id'], data={'user_id': args.to_user_id})
            logging.info('updated opportunity %s' % opportunity['id'])

        offset += max(0, len(opportunities) - 1)
        has_more = resp['has_more']
