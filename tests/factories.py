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

    def delete_all_tasks(self):
        has_more = True

        task_ids = []
        while has_more:
            resp = self.api.get('task', data={
                '_fields': 'id'
            })

            tasks = resp['data']

            for task in tasks:
                task_ids.append(task['id'])

            has_more = resp['has_more']

        for task_id in task_ids:
            self.api.delete('task/' + task_id)
            logging.info("deleted task %s", task_id)
        logging.info("deleted all tasks")

    def delete_all_opportunities(self):
        has_more = True

        opportunity_ids = []
        while has_more:
            resp = self.api.get('opportunity', data={
                '_fields': 'id'
            })

            opportunities = resp['data']

            for opportunity in opportunities:
                opportunity_ids.append(opportunity['id'])

            has_more = resp['has_more']

        for opportunity_id in opportunity_ids:
            self.api.delete('opportunity/' + opportunity_id)
            logging.info("deleted opportunity %s", opportunity_id)
        logging.info("deleted all opportunities")

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

    def lead(self):
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
        response = self.api.post('lead', data=lead)
        logging.info("created lead %s", response)
        return response

    def task(self, lead_id, assigned_to, complete=False):
        task = {
            "_type": "lead",
            "lead_id": lead_id,
            "assigned_to": assigned_to,
            "text": fake.name(),
            "date": fake.date(pattern="%Y-%m-%d"),
            "is_complete": complete,
        }
        response = self.api.post('task', data=task)
        logging.info("created task %s", response)
        return response 

    def opportunity(self, lead_id, user_id, status="Active"):
        opportunity = {
            "note": fake.name(),
            "lead_id": lead_id,
            "status": status,
            "user_id": user_id,
        }
        response = self.api.post('opportunity', data=opportunity)
        logging.info("created opportunity %s", response)
        return response 




