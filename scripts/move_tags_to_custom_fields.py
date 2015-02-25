import argparse
import csv
from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='Splits up a "Tags" custom field into separate custom fields, as described by a CSV file with columns "tag", "custom_field_name", "custom_field_value"')
parser.add_argument('csvfile', type=argparse.FileType('rU'), help='csv file')
parser.add_argument('--api-key', '-k', required=True, help='API Key')
parser.add_argument('--development', '-d', action='store_true',
                    help='Use a development (testing) server rather than production.')

args = parser.parse_args()

# Dict of lowercased tags => tuples of (custom_field_name, custom_field_value)
tag_templates = {}

sniffer = csv.Sniffer()
dialect = sniffer.sniff(args.csvfile.read(1024))
args.csvfile.seek(0)
c = csv.DictReader(args.csvfile, dialect=dialect, fieldnames=['tag', 'custom_field_name', 'custom_field_value'])
c.next()
for r in c:
    if r:
        assert len(r) == 3, 'Invalid csv format at line %d' % (c.line_num,)
        tag_templates[r['tag'].lower()] = (r['custom_field_name'], r['custom_field_value'])

api = CloseIO_API(args.api_key, development=args.development)
has_more = True
offset = 0

while has_more:
    resp = api.get('lead', data={
        'query': 'custom.Tags:* sort:created',
        '_skip': offset,
        '_fields': 'id,custom'
    })

    leads = resp['data']

    for l in leads:
        if 'Tags' in l['custom'].keys():
            tags = [t.strip() for t in l['custom']['Tags'].split(',')]
            new_fields = {}
            for t in tags:
                t_lower = t.lower()
                if t_lower in tag_templates.keys():
                    new_fields['custom.' + tag_templates[t_lower][0]] = tag_templates[t_lower][1]

            print l['id'], 'Tags:', l['custom']['Tags']
            print '...', new_fields
            api.put('lead/'+l['id'], data=new_fields)

    offset += max(0, len(leads) - 1)
    has_more = resp['has_more']
