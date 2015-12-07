#!/usr/bin/env python
import argparse
from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='Detect duplicates & merge leads (see source code for details)')
parser.add_argument('--api-key', '-k', required=True, help='API Key')
parser.add_argument('--development', action='store_true', help='Use a development (testing) server rather than production.')
parser.add_argument('--confirmed', action='store_true', help='Without this flag, no action will be taken (dry run). Use this to perform the merge.')
args = parser.parse_args()

"""
Detect duplicate leads and merge them.

Duplicate criteria:
- Case insensitive exact match by Company Name

Priority (how to choose 'Destination lead'):
- Prefers leads with Opportunities over ones without.
- If both or neither have opportunities, prefer leads with desired_status specified below.
"""

desired_status = 'open' # capitalization doesn't matter

api = CloseIO_API(args.api_key, development=args.development)
has_more = True
offset = 0
last_lead = None
total_merged = 0

while has_more:
    leads_merged_this_page = 0

    # Get a page of leads
    resp = api.get('lead', data={
        'query': 'sort:display_name',
        '_skip': offset,
        '_fields': 'id,display_name,name,status_label,opportunities,custom'
    })
    leads = resp['data']

    for lead in leads:

        if last_lead and lead['id'] == last_lead['id']:
            continue # same lead, skip

        # Determine whether "lead" should be considered a duplicate of the previous lead ("last_lead")
        last_lead_name = (last_lead['name'] or '').strip().lower() if last_lead else ''
        lead_name = (lead['name'] or '').strip().lower()
        is_duplicate = last_lead and lead_name and last_lead_name == lead_name

        if is_duplicate:

            # Should we use 'lead' or 'last_lead' as the 'destination' (preferred) lead?
            prefer_last_lead = True
            if lead['opportunities'] and not last_lead['opportunities']:
                prefer_last_lead = False
            elif lead['status_label'].lower() == desired_status.lower() and last_lead['status_label'].lower() != desired_status.lower():
                prefer_last_lead = False

            if prefer_last_lead:
                destination_lead = last_lead
                source_lead = lead
            else:
                destination_lead = lead
                source_lead = last_lead

            print 'Duplicate (preferring 1st one: %s)' % prefer_last_lead
            print last_lead
            print lead
            print ''

            if args.confirmed:

                # Merge the leads using the 'Merge Leads' API endpoint
                api.post('lead/merge', data={
                    'source': source_lead['id'],
                    'destination': destination_lead['id'],
                })
                leads_merged_this_page += 1
                total_merged += 1

                last_lead = destination_lead
                continue

        last_lead = lead

    # In order to make sure we don't skip any possible duplicates at the per-page boundry, we subtract offset
    # by one each time so there's an overlap. We also subtract the number of leads merged since those no longer exist.
    offset += max(0, len(leads) - 1 - leads_merged_this_page)
    has_more = resp['has_more']

print 'Done; %d merges made' % total_merged
