#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import os
import time
import argparse

from closeio_api import Client as CloseIO_API, APIError
from scripts import user_reassign
from factories import Factory
import utils

api_key = os.getenv("CLOSEIO_API_KEY")


class TesUserReassign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = CloseIO_API(api_key)
        cls.factory = Factory(cls.api)
        cls.user1 = cls.api.get('me', data={'_fields': 'id,email,memberships'})

        organization_id = cls.user1['memberships'][0]['organization_id']
        organization = cls.api.get('organization/' + organization_id, data={'_fields': 'memberships'})
        membershipsRemoveMe = [m for m in organization["memberships"] if m["user_id"] != cls.user1["id"]]
        user2_id = membershipsRemoveMe[0]["user_id"]
        cls.user2 = cls.api.get('user/' + user2_id, data={'_fields': 'id,email'})

    def setUp(self):
        self.factory.delete_all_leads()
        self.factory.delete_all_tasks()
        self.factory.delete_all_opportunities()

        lead = self.factory.lead()
        self.task1 = self.factory.task(lead['id'], self.user1["id"], complete=False)
        self.task2 = self.factory.task(lead['id'], self.user1["id"], complete=True)
        self.opportunity1 = self.factory.opportunity(lead['id'], self.user1["id"], status='Active')
        self.opportunity2 = self.factory.opportunity(lead['id'], self.user1["id"], status='Won')

        self.args = argparse.Namespace()
        self.args.from_user_email = self.user1["email"]
        self.args.to_user_email = self.user2["email"]
        self.args.tasks = False
        self.args.all_tasks = False
        self.args.opportunities = False
        self.args.all_opportunities = False
        self.args.confirmed = True

        time.sleep(1)

    def test_run_reassign_tasks(self):
        self.args.tasks = True
        user_reassign.task(api=self.api, args=self.args)
        
        time.sleep(1)

        updatedTask1 = self.api.get('task/' + self.task1["id"])
        self.assertEqual(self.user2["id"], updatedTask1["assigned_to"])

        updatedTask2 = self.api.get('task/' + self.task2["id"])
        self.assertEqual(self.user1["id"], updatedTask2["assigned_to"])

    def test_run_reassign_all_tasks(self):
        self.args.all_tasks = True
        user_reassign.task(api=self.api, args=self.args)
        
        time.sleep(1)

        updatedTask1 = self.api.get('task/' + self.task1["id"])
        self.assertEqual(self.user2["id"], updatedTask1["assigned_to"])

        updatedTask2 = self.api.get('task/' + self.task2["id"])
        self.assertEqual(self.user2["id"], updatedTask2["assigned_to"])

    def test_run_reassign_opportunities(self):
        self.args.opportunities = True
        user_reassign.task(api=self.api, args=self.args)
        
        time.sleep(1)

        updateOpportunity1 = self.api.get('opportunity/' + self.opportunity1["id"])
        self.assertEqual(self.user2["id"], updateOpportunity1["user_id"])

        updateOpportunity2 = self.api.get('opportunity/' + self.opportunity2["id"])
        self.assertEqual(self.user1["id"], updateOpportunity2["user_id"])

    def test_run_reassign_all_opportunities(self):
        self.args.all_opportunities = True
        user_reassign.task(api=self.api, args=self.args)
        
        time.sleep(1)

        updateOpportunity1 = self.api.get('opportunity/' + self.opportunity1["id"])
        self.assertEqual(self.user2["id"], updateOpportunity1["user_id"])

        updateOpportunity2 = self.api.get('opportunity/' + self.opportunity2["id"])
        self.assertEqual(self.user2["id"], updateOpportunity2["user_id"])


if __name__ == '__main__':
    unittest.main()
