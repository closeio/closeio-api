import argparse
import csv
from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='uploads custom fields from csv')
parser.add_argument('csvfile', type=argparse.FileType('r'), help='csv file')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--development', '-d', action='store_true', help='Use a development (testing) server rather than production.')

args = parser.parse_args()

tag_templates = {}

sniffer = csv.Sniffer()
dialect = sniffer.sniff(args.csvfile.read(1024))
args.csvfile.seek(0)
c = csv.DictReader(args.csvfile, dialect=dialect, fieldnames=['tag', 'custom_field_name', 'custom_field_value'])
c.next()
for r in c:
    if r:
        assert len(r) == 3, 'Invalid csv format'
        tag_templates[r['tag']] = (r['custom_field_name'], r['custom_field_value'])


api = CloseIO_API(args.api_key, development=args.development)
has_more = True
offset = 0

while has_more:
    resp = api.get('lead', data={
        'query': 'sort:created',
        '_skip': offset,
        '_fields': 'id,custom'
    })

    leads = resp['data']

    for l in leads:
        if 'Tags' in l['custom'].keys():
            tags = [t.strip() for t in l['custom']['Tags'].split(',')]
            new_fields = {}
            for t in tags:
                if t in tag_templates.keys():
                    new_fields['custom.' + tag_templates[t][0]] = tag_templates[t][1]

            api.put('lead/'+l['id'], data=new_fields)

    offset += max(0, len(leads) - 1)
    has_more = resp['has_more']
