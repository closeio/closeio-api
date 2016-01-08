#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import csv
from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(description='Creates or updates a custom choices field')
parser.add_argument('--api-key', '-k', required=True, help='API Key.')
parser.add_argument('csvfile', type=argparse.FileType('rU'), help='Path to csv file.')
parser.add_argument('fieldname', help='Custom field name to update.')
parser.add_argument('--update', action='store_true', help="Update an existing custom choices field.")
parser.add_argument('--overwrite', action='store_true', help="Overwrite existing choices if update is selected.")
args = parser.parse_args()

data = []
api = CloseIO_API(args.api_key)

# Get current custom field information.
resp = api.get('custom_fields/lead')
fields = resp['data']

fieldid = None

# Searches for a matching custom field name and sets fieldid if found.
# If --update is used without --overwrite the data list gets set to the current custom field's choices.
for field in fields:
	if field['name'].lower() == args.fieldname.lower():
		fieldid = field['id']
		if not args.overwrite:
			data = field['choices']
		if field['type'] != 'choices' and args.update:
			print 'Error: ' + args.fieldname + ' does not have a choices field type.'
			sys.exit(1)

# Errors if creating and field is found or if updating and the field is not found.
if fieldid and not args.update:
	print 'Error: '+args.fieldname+' already exists.  Choose another name or use --update to update current choices.'
	sys.exit(1)
elif not fieldid and args.update:
	print 'Error: ' + args.fieldname + ' not found.  Remove --update if you wish to create a new field with this name.'
	sys.exit(1)

	
# Reads our CSV file and appends it to our data list.
# The data list should be empty unless --update is used without --overwrite.
c = csv.reader(args.csvfile, delimiter=',', quotechar='"')

for r in c:
	if r[0] != '':
		data.append(r[0])

# Uses post to create a new field if creating and uses put to update an existing field if updating.
if not args.update:
	api.post('custom_fields/lead', data={'name': args.fieldname, 'type': 'choices', 'choices': data})
	print 'Successfully created ' + args.fieldname + '!'
else:
	api.put('custom_fields/lead/'+fieldid, data={'choices': data})
	print 'Successfully updated ' + args.fieldname + '!'
