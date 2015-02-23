#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import logging

from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='Assigns tasks or opportunities from one user to another')
parser.add_argument('--from-user-id', '-f', type=str, help='')
parser.add_argument('--to-user-id', '-t', type=str, help='')
parser.add_argument('--api_key', '-k', required=True, help='')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')
parser.add_argument('--confirmed', '-c', action='store_true',
                    help='Without this flag, the script will do a dry run without actually updating any data.')
group = parser.add_argument_group()
group.add_argument('--tasks', '-T', action='store_true',
                   help='')
group.add_argument('--opportunities', '-O', action='store_true',
                   help='')

args = parser.parse_args()

if not args.tasks and not args.opportunities:
    parser.error("at least one of --tasks and --opportunities required")

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
if args.tasks:
    has_more = True
    offset = 0
    while has_more:
        resp = api.get('task', data={
            'assigned_to': args.from_user_id,
            '_order_by': 'date_created',
            '_skip': offset,
            '_fields': 'id,assigned_to'
        })

        tasks = resp['data']
        for task in tasks:
            if args.confirmed:
                api.put('task/'+task['id'], data={'assigned_to': args.to_user_id})
            logging.info('updated task %s' % task['id'])

        offset += max(0, len(tasks) - 1)
        has_more = resp['has_more']

# opportunities
if args.opportunities:
    has_more = True
    offset = 0
    while has_more:
        resp = api.get('opportunity', data={
            'query': 'user_id:"%s" sort:date_created' % args.from_user_id,
            '_skip': offset,
            '_fields': 'id,assigned_to'
        })

        opportunities = resp['data']
        for opportunity in opportunities:
            if args.confirmed:
                api.put('opportunity/'+opportunity['id'], data={'user_id', args.to_user_id})
            logging.info('updated opportunity %s' % task['id'])

        offset += max(0, len(opportunities) - 1)
        has_more = resp['has_more']
