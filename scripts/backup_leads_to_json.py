#!/usr/bin/env python
import json
import codecs
from client.api import CloseIO_API


"""
Dumps all leads within a given organization to a file in JSON format
"""

api_key = raw_input("API key: ")
file_name = raw_input("Output Filename: ")

api = CloseIO_API(api_key)

f = codecs.open(file_name, "w", "utf-8")

leads = []
has_more = True
offset = 0
while has_more:
    resp = api.get('lead', data={'_skip': offset})
    data = resp['data']
    for lead in data:
        leads.append(lead)
    offset += len(data)
    has_more = resp['has_more']

json.dump(leads, f)
f.close()
