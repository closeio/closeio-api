#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from utils import loop_over_changing_resultset, TaskRunner


if __name__ == '__main__':
    task_runner = TaskRunner(description='Delete all but first address for leads with multiple addresses.', task=task)
    task_runner.parser.add_argument('--limit', '-l', help='Limit number of items per page', type=int, default=100)
    task_runner.run()


def task(api, args):
    def filter_leads_with_multiple_addresses():
        return api.get('lead', data={
            'query': "addresses > 1 sort:activities",
            '_fields': 'id,addresses',
            '_limit': args.limit,
        })

    for leads in loop_over_changing_resultset(filter_leads_with_multiple_addresses):
        for lead in leads:
            if len(lead['addresses']) < 2:
                logging.warning("unexpected result: %s", lead)
                continue # this shouldn't happen based on the search query, but just to be safe...
            api.put('lead/' + lead['id'], data={'addresses': lead['addresses'][:1]})
            logging.info("removed %d extra address(es) for %s\n%s" % (len(lead['addresses'][1:]), lead['id'], lead['addresses'][1:]))
