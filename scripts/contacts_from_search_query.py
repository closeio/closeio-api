#!/usr/bin/env python
import argparse
from flask_common.utils import CsvWriter
from closeio_api import Client as CloseIO_API

HEADERS = ['lead_name', 'contact_name', 'title', 'primary_email', 'primary_phone']

parser = argparse.ArgumentParser(description='Exports the primary contact information for each contact to CSV based on search query')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--query', '-q', required=True, help='Search Query')
parser.add_argument('--output', '-o', required=True, help='Output Filename')
args = parser.parse_args()

with open(args.output, 'wb') as f:
    writer = CsvWriter(f)
    api = CloseIO_API(args.api_key)

    # get the org id necessary for search
    org_id = api.get('api_key')['data'][0]['organization_id']

    # get all the search results for given lead name
    search_results = []
    filters = {
        'organization_id': org_id,
        'query': args.query,
        '_fields': 'id,name,contacts'
    }

    writer.writerow(HEADERS)

    skip = 0
    limit = 100
    has_more = True

    while has_more:
        filters['_skip'] = skip
        filters['_limit'] = limit
        leads = api.get('lead', data=filters)['data']
        for lead in leads:
            for contact in lead['contacts']:
                
                phones = contact['phones'] 
                emails = contact['emails'] 
                primary_phone = phones[0]['phone'] if phones else None
                primary_email = emails[0]['email'] if emails else None

                row = [lead['name'], contact['name'], contact['title'], primary_email, primary_phone]
                writer.writerow(row)

        if len(leads) < limit:
            break
        skip += limit
