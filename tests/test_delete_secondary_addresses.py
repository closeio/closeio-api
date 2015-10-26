#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import os
import time

from closeio_api import Client as CloseIO_API, APIError
from scripts import delete_secondary_addresses
from factories import Factory
import utils

api_key = os.getenv("CLOSEIO_API_KEY")


class TestDeleteSecondaryAddresses(unittest.TestCase):
    def setUp(self):
        self.api = CloseIO_API(api_key)
        self.factory = Factory(self.api)
        self.factory.delete_all_leads()

    def test_run(self):
        for i in range(3):
            self.factory.lead_with_addresses(1)
        for i in range(6):
            self.factory.lead_with_addresses(2)

        time.sleep(1.5)

        delete_secondary_addresses.run(api_key=api_key, development=False, confirmed=True, limit=3)

        time.sleep(1.5)

        leads = list(utils.all(self.api, fields="id,addresses"))
        self.assertEqual(9, len(leads))
        for lead in leads:
            self.assertEqual(1, len(lead['addresses']), "lead %s has too many addresses" % lead)


if __name__ == '__main__':
    unittest.main()
