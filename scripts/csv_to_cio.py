#!/usr/bin/env python

import argparse
import time
from progressbar import ProgressBar
from progressbar.widgets import Percentage, Bar, ETA, FileTransferSpeed
from requests.models import ConnectionError
from api import CloseIO_API, APIError
from utils import CsvReader, count_lines, title_case, uncamel

parser = argparse.ArgumentParser(description='Import leads from CSV file')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--development', action='store_true', help='Use a development server rather than production.')
parser.add_argument('file', help='Path to the csv file')
args = parser.parse_args()

reader = CsvReader(args.file)

header = reader.next() # skip the 1st line header

import_count = count_lines(args.file) # may have no trailing newline

progress_widgets = ['Importing %d rows: ' % import_count, Percentage(), ' ', Bar(),
           ' ', ETA(), ' ', FileTransferSpeed()]

pbar = ProgressBar(widgets=progress_widgets, maxval=import_count).start()

cnt = 0
success_cnt = 0

##############################################################################
#                          MAKE CHANGES HERE                                 #
##############################################################################
# Default Template CSV schema: Company name[0], url[1], status[2], email[3], phone[4], contact name[5], contact title[6], address[7], city[8], state[9], zip[10], country[11], custom fields [12, 13, ...]
# check for custom fields

unique_leads = {}

custom_headers = []
if len(header) > 12:
    custom_headers = [{ 'label': header[i].replace(' ', ''), 'index': i } for i in range(12, len(header), 1)]

for i, row in enumerate(reader):
    row = [elem.strip() for elem in row]  # strip unnecessary white spaces

    # check if the row isn't empty
    has_data = [elem for elem in row if elem]
    if not has_data:
        continue

    lead = {
        'name': row[0],
        'url': row[1],
        'status': row[2] or 'potential',

        'contacts': [],

        'custom': {}
    }

    # custom fields
    for field in custom_headers:
        if row[field['index']]:
            lead['custom'][field['label']] = row[field['index']]

    # address
    if row[8] or row[9] or row[10] or row[11]:
        lead['addresses'] = [{}]
    if row[8]:
        lead['addresses'][0]['city'] = title_case(row[8])
    if row[9]:
        lead['addresses'][0]['state'] = row[9]
    if row[10]:
        lead['addresses'][0]['zipcode'] = row[10]
    if row[11]:
        lead['addresses'][0]['country'] = row[11]

    if row[5] or row[6] or row[4] or row[3]:
        contact = {}
        if row[5]:
            contact['name'] = uncamel(row[5])
        if row[6]:
            contact['title'] = row[6]
        if row[4]:
            contact['phones'] = [
                {
                    'phone': row[4],
                    'type': 'office'
                }
            ]
        if row[3]:
            contact['emails'] = [
                {
                    'email': row[3],
                    'type': 'office'
                }
            ]
        lead['contacts'].append(contact)

    # group by lead Name (company) if possible, otherwise put each row in its own lead
    grouper = lead['name'] if lead['name'] else ('row-num-%s' % i)

    if lead['name'] not in unique_leads:
        unique_leads[grouper] = lead
    else:
        unique_leads[grouper]['contacts'].extend(lead['contacts'])

##############################################################################


api = CloseIO_API(args.api_key, development=args.development)

for key, val in unique_leads.items():
    retries = 5
    while retries > 0:
        try:
            retries -= 1
            api.post('lead', val)
            retries = 0
            success_cnt += 1
        except APIError, err:
            print 'An error occurred while saving "%s"' % key
            print err
            retries = 0
        except ConnectionError, e:
            print 'Connection error occurred, retrying... (%d/5)' % retries
            if retries == 0:
                raise
            time.sleep(2)

    cnt += 1
    if cnt > import_count:
        print 'Warning: count overflow'
        cnt = import_count
    pbar.update(cnt)

pbar.finish()

print 'Successful responses: %d of %d' % (success_cnt, len(unique_leads))

