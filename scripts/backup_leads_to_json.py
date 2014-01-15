#!/usr/bin/env python
import json
import codecs
from closeio_api import Client as CloseIO_API

"""
Dumps all leads within a given organization to a file in JSON format, including activities
"""

api_key = raw_input("API key: ")
file_name = raw_input("Output Filename: ")

api = CloseIO_API(api_key)

output = []
has_more = True
offset = 0

with codecs.open(file_name, "w", "utf-8") as f:
    while has_more:
        resp = api.get('lead', data={'_skip': offset})
        leads = resp['data']

        offset += len(leads)
        has_more = resp['has_more']

        for lead in leads:
            more_activities = True
            activities_offset = 0
            lead['activities'] = []

            while more_activities:
                resp = api.get('activity', data={'lead_id': lead['id'], '_skip': activities_offset})
                activities = resp['data']
                lead['activities'].extend(activities)
                activities_offset += len(activities)
                more_activities = resp['has_more']

            output.append(lead)

    json.dump(output, f)
