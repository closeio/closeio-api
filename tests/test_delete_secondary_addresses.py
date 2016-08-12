#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import os
import time
import argparse

from closeio_api import Client as CloseIO_API, APIError
from scripts import delete_secondary_addresses
from scripts.utils import CloseIO_API_Wrapper, loop_over_stable_resultset
from factories import Factory


api_key = os.getenv("CLOSEIO_API_KEY")


class TestDeleteSecondaryAddresses(unittest.TestCase):
    def setUp(self):
        real_api = CloseIO_API(api_key)
        self.api = CloseIO_API_Wrapper(real_api, paranoid=False)
        self.factory = Factory(self.api)
        self.factory.delete_all_leads()

    def test_run(self):
        for i in range(3):
            self.factory.lead_with_addresses(1)
        for i in range(3):
            self.factory.lead_with_addresses(2)
        for i in range(3):
            self.factory.lead_with_addresses(3)

        time.sleep(1.5)

        args = argparse.Namespace()
        args.limit = 3
        delete_secondary_addresses.task(api=self.api, args=args)

        time.sleep(1.5)

        leads = list(fetch_all_leads(self.api, fields="id,addresses"))
        self.assertEqual(9, len(leads))
        for lead in leads:
            self.assertEqual(1, len(lead['addresses']), "lead %s has too many addresses" % lead)


def fetch_all_leads(api, query='*', fields='id'):
    def search_leads():
        return api.get('lead', data={
            'query': query,
            '_fields': fields,
        })

    for leads in loop_over_stable_resultset(search_leads):
        print leads
        for lead in leads:
            yield lead

if __name__ == '__main__':
    unittest.main()
