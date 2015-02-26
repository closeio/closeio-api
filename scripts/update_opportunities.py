import argparse
import sys

from closeio_api import Client as CloseIO_API


parser = argparse.ArgumentParser(description="Change all the opportunities for a given leads' search query to a given status.")
parser.add_argument('--query', type=str, required=True, help='Search query.')
parser.add_argument('--api_key', type=str, required=True, help='API key')
parser.add_argument('--status', type=str, required=True, help='Label of the new status')
parser.add_argument('--dev', action='store_true', help='Use the dev server', default=False)
args = parser.parse_args()

# Should tell you how many leads are going to be affected
api = CloseIO_API(args.api_key, development=args.dev)

# Get the status_id
org_id = api.get('api_key')['data'][0]['organization_id']
statuses = api.get('organization/{0}'.format(org_id))['opportunity_statuses']
new_status_id = [st['id'] for st in statuses if st['label'].lower() == args.status.lower()]
if not new_status_id:
    print 'Status not found: {0}'.format(args.status)
    sys.exit(1)

new_status_id = new_status_id[0]

print 'Gathering opportunities for {0}'.format(args.query)

has_more = True
offset = 0
limit = 50
opp_ids = []

while has_more:
    resp = api.get('lead', data={'_skip': offset, '_limit': limit, 'query': args.query})
    opp_ids.extend([opp['id'] for lead in resp['data'] for opp in lead['opportunities']])
    has_more = resp['has_more']
    offset += limit

ans = raw_input('{0} opportunities found. Do you want to update all of them to {1}? (y/n): '.format(len(opp_ids), args.status))
if ans.lower() != 'y':
    sys.exit(0)

print 'Updating opportunities to {0}'.format(args.status)

# Update opps
for opp_id in opp_ids:
    resp = api.put('opportunity/{0}'.format(opp_id), data={'status_id': new_status_id})

print 'Done!'

