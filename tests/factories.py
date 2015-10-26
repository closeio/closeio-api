#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from faker import Factory


fake = Factory.create()
logging.basicConfig(level=logging.INFO)


class Factory(object):
    """docstring for Factory"""
    def __init__(self, api):
        self.api = api

    def delete_all_leads(self):
        has_more = True

        lead_ids = []
        while has_more:
            resp = self.api.get('lead', data={
                'query': '*',
                '_fields': 'id'
            })

            leads = resp['data']

            for lead in leads:
                lead_ids.append(lead['id'])

            has_more = resp['has_more']

        for lead_id in lead_ids:
            self.api.delete('lead/' + lead_id)
            logging.info("deleted lead %s", lead_id)
        logging.info("deleted all leads")

    def lead_with_addresses(self, addresses_count=1):
        name = fake.company()
        lead = {
            "display_name": name,
            "addresses": [],
            "name": name,
            "contacts": [],
            "custom": {},
            "url": None,
            "description": fake.catch_phrase(),
        }
        for i in range(addresses_count):
            address = {
                "label": "business",
                "address_1": fake.street_address(),
                "address_2": fake.secondary_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "zipcode": fake.zipcode(),
                "country": fake.country_code(),
            }
            lead['addresses'].append(address)

        self.api.post('lead', data=lead)
        logging.info("created lead %s", lead)


