#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import time

from closeio_api import Client as CloseIO_API, APIError


def loop_over_stable_resultset(api_call):
    has_more = True
    while has_more:
        resp = api_call()
        yield resp['data']
        has_more = resp['has_more']


class CloseIO_API_Wrapper(object):
    """paranoid: boolean = if True don't send non-GET API calls if script isn't confirmed."""
    def __init__(self, api, paranoid):
        self.api = api
        self.paranoid = paranoid

    # delegate methods to the api instance
    def __getattr__(self, attr):
        func = getattr(self.__dict__, attr) if attr in self.__dict__ else None
        if callable(func):
            return func
        if self.paranoid and attr != "get":
            # fake a callable (don't throw an exception to make it easy to use )
            return lambda *args, **kwargs: logging.info("FAKE {} {} {}".format(attr.upper(), args[0], kwargs))
        return getattr(self.api, attr)

    def sleep(self, seconds, reason):
        logging.info(reason)
        if not self.paranoid:
            time.sleep(2)

    def loop_over_changing_resultset(self, api_call):
        for result in loop_over_stable_resultset(api_call):
            yield result
            self.sleep(seconds=2, reason="Pausing for 2s to give the search indexer some time to catch up with the changes")



class TaskRunner(object):
    def __init__(self, description, task):
        self.task = task
        self.parser = argparse.ArgumentParser(description=description)
        self.parser.add_argument('--api-key', '-k', required=True, help='')
        self.parser.add_argument('--confirmed', '-c', action='store_true',
                            help='Without this flag, the script will do a dry run without actually updating any data.')
        self.parser.add_argument('--development', '-d', action='store_true',
                            help='Use a development (testing) server rather than production.')

    def run(self):
        args = self.parser.parse_args()
        log_format = "[%(asctime)s] %(levelname)s %(message)s"
        if not args.confirmed:
            log_format = 'DRY RUN: ' + log_format

        logging.basicConfig(level=logging.INFO, format=log_format)
        logging.debug('parameters: %s' % vars(args))

        real_api = CloseIO_API(args.api_key, args.development)
        api = CloseIO_API_Wrapper(real_api, paranoid=not args.confirmed)

        self.task(api=api, args=args)
