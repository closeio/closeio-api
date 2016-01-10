#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import csv
from closeio_api import Client as CloseIO_API

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="""
Creates new custom choices fields or updates/replaces existing choices for custom choices fields.
Header's columns may be declared in any order. Detects csv dialect (delimeter and quotechar).

By default a three column csv file is used.  See below for header information.

Optionally a single row headerless csv file can be used for a single field update.
Use the single_field_name and single_field_action values for a single field update.
""", epilog="""
columns:
    * field_name                       - Name of field to be created or updated.

    * choice                           - Choice to be added to field

    * action                           - Create will create a new custom field with the choices in your csv.
                                       - Update will update an existing field and add to the existing choices.
                                       - Replace will replace all of the existing values for a field with
                                         the values contained in your csv.
""")
parser.add_argument('csvfile', type=argparse.FileType('rU'), help='Path to csv file.')
parser.add_argument('single_field_name', nargs='?', help='Optional: Field name to use for a single field update.')
parser.add_argument('single_field_action', nargs='?', help='Optional: Action to use for a single field update.')
parser.add_argument('--api-key', '-k', required=True, help='API Key.')
parser.add_argument('--confirmed', '-c', action='store_true', help='Without this flag, the script will do a dry run without actually updating any data.')
args = parser.parse_args()

api = CloseIO_API(args.api_key)

action_data = {}
choices_data = {}

# Checks if our single field update values are set.
# Formats the information from the variables and the csv file into the same dictionary format as the multi-column section.
if args.single_field_name and args.single_field_action:

	if args.single_field_action.lower().strip() not in ('create', 'update', 'replace'):
		print 'Error: ' + r['action'] + ' not a valid action.'
		print 'Use create, update, or replace only.'
		sys.exit(1)

	action_data[args.single_field_name] = args.single_field_action.lower().strip()
	choices_data[args.single_field_name] = []
	
	c = csv.reader(args.csvfile, delimiter=',', quotechar='"')
	
	for r in c:
		if r[0] != '':
			choices_data[args.single_field_name].append(r[0].strip())

# Multi-column csv import.
# Reads our csv and processes the information into two dictionaries with field_name as the key in both.
else:
	sniffer = csv.Sniffer()
	dialect = sniffer.sniff(args.csvfile.read(1024))
	args.csvfile.seek(0)
	c = csv.DictReader(args.csvfile, dialect=dialect, fieldnames=['field_name', 'choice', 'action'])
	assert any(x in ('field_name', 'choice', 'action') for x in c.fieldnames), \
		'ERROR: column "field_name", "choice" or "action" is not found'
	c.next()

	for r in c:
		if r:
			assert len(r) == 3, 'Invalid csv format at line %d' % (c.line_num,)
		
			if r['field_name'].lower().strip() in str(choices_data.keys()).lower().strip():
				if r['field_name'] not in choices_data:
					print 'Error: Mixed case detected for field_name: ' + r['field_name'] + ' on line %d.' % (c.line_num,)
					sys.exit(1)
				elif r['action'].lower().strip() != action_data[r['field_name']].lower().strip():
					print 'Error: ' + r['action'] + ' and ' + action_data[r['field_name']] + ' have been specified for ' + r['field_name'] + '.'
					print 'Please specify only one action type per field_name.'
					sys.exit(1)
				
				choices_data[r['field_name']].append(r['choice'])
			else:
				if r['action'].lower().strip() not in ('create', 'update', 'replace'):
					print 'Error: ' + r['action'] + ' not a valid action.'
					print 'Use create, update, or replace only.'
					sys.exit(1)
					
				action_data[r['field_name']] = (r['action'].lower().strip())
				choices_data[r['field_name']] = [r['choice']]


# Pulls our existing custom field information.		
resp = api.get('custom_fields/lead')
fields = resp['data']

for field_name, action in action_data.items():
	field_id = None
	
	#Checks if our field_name already exists in our org.
	#If updating the field_id is saved.
	#If creating then a existing field throws an error.
	for field in fields:
		if field['name'].lower().strip() == field_name.lower().strip():
			field_id = field['id']
			
			if action == 'update':
				choices_data[field_name].extend(field['choices'])
			
			if action == 'create':
				print 'Error: '+ field_name +' already exists.  Choose another name or use update or replace.'
				sys.exit(1)
			elif field['type'] != 'choices':
				print 'Error: ' + field_name + ' does not have a choices field type.'
				sys.exit(1)
	
	if not field_id and action in ('update', 'replace'):
		print 'Error: ' + field_name + ' not found.  Remove --update if you wish to create a new field with this name.'
		sys.exit(1)
	
	
	# Only runs against the org if --confirmed is used.
	# Uses post for creating and put for update/replace
	if args.confirmed:
		if action == 'create':
			api.post('custom_fields/lead', data={'name': field_name, 'type': 'choices', 'choices': choices_data[field_name]})
			print 'Successfully created ' + field_name + '!'
		else:
			api.put('custom_fields/lead/'+field_id, data={'choices': choices_data[field_name]})
			if action == 'update':
				print 'Successfully updated existing values for ' + field_name + '!'
			else:
				print 'Successfully replaced existing values for ' + field_name + '!'
	else:
		print 'No problems detected with ' + field_name + '!'
		print 'Use --confirmed if you wish to run these changes against your Close.io org.'