#!/usr/bin/env python

import time, argparse, re, unidecode, sys, json
from progressbar import ProgressBar
from progressbar.widgets import Percentage, Bar, ETA, FileTransferSpeed
from requests.exceptions import ConnectionError
from closeio_api.api import CloseIO_API, APIError
from closeio_api.utils import CsvReader, count_lines, title_case, uncamel

parser = argparse.ArgumentParser(description='Import leads from CSV file')
parser.add_argument('--api_key', '-k', required=True, help='API Key')
parser.add_argument('--skip_duplicates', action='store_true', help='Skip leads that are already present in Close.io (determined by company name).')
parser.add_argument('--no_grouping', action='store_true', help='Turn off the default group-by-company behavior.')
parser.add_argument('--development', action='store_true', help='Use a development server rather than production.')
parser.add_argument('file', help='Path to the csv file')
args = parser.parse_args()

reader = CsvReader(args.file)

header = reader.next() # skip the 1st line header

import_count = count_lines(args.file) # may have no trailing newline

cnt = success_cnt = 0

def slugify(str, separator='_'):
    str = unidecode.unidecode(str).lower().strip()
    return re.sub(r'\W+', separator, str).strip(separator)

# Look for headers/columns that match these, case-insensitive. All other headers will be treated as custom fields.
expected_headers = (
    'company', # multiple contacts will be grouped if company names match
    'url',
    'status',
    'contact', # name of contact
    'title',
    'email',
    'phone', # recommended to start with "+" followed by country code (e.g., +1 650 555 1234)
    'mobile_phone',
    'fax',
    'address',
    'address_1', # if address is missing, address_1 and address_2 will be combined to create it.
    'address_2', # if address is missing, address_1 and address_2 will be combined to create it.
    'city',
    'state',
    'zip',
    'country',
)

# remove trailing empty column headers
while not len(header[-1].strip()):
    del header[-1]

if len(set(header)) != len(header):
    raise Exception('Cannot have duplicate column header names')

normalized_headers = [slugify(col) for col in header]

if len(set(normalized_headers)) != len(normalized_headers):
    raise Exception('After column header names were normalized there were duplicate column header names')

# build a map of header names -> index in actual header row
header_indices   = { col: i for (i, col) in enumerate(normalized_headers) } # normalized columns as keys
header_indices.update({ col: i for (i, col) in enumerate(header) }) # add in original column names as keys
expected_headers = [ col for col in normalized_headers if col in expected_headers ]
custom_headers = list(set(normalized_headers) - set(expected_headers)) # non-recognized fields in slug-ed format

# restore original version (capitalization) to custom fields
custom_headers = [ header[header_indices[normalized_col]] for normalized_col in custom_headers ]

print "\nRecognized these column names:"
print '> %s' % ', '.join(expected_headers)
if len(custom_headers):
    print "\nThe following column names weren't recognized, and will be imported as custom fields:"
    print '> %s' % ', '.join(custom_headers)
    print ''

def value_in_row(row, field):
    # "row" is a list representing one row from the CSV
    # "field" should be a string in "expected_headers"
    try:
        return row[header_indices[field]]
    except Exception as e:
        return None

def lead_from_row(row):
    row = [elem.strip() for elem in row]  # strip unnecessary white spaces

    # check if the row isn't empty
    has_data = [elem for elem in row if elem]
    if not has_data:
        return None

    lead = {
        'name': value_in_row(row, 'company'),
        'contacts': [],
        'custom': {}
    }

    if value_in_row(row, 'url'):
        lead['url'] = value_in_row(row, 'url')

    if value_in_row(row, 'status'):
        lead['status'] = value_in_row(row, 'status')

    if lead.get('url') and '://' not in lead['url']:
        lead['url'] = 'http://%s' % lead['url']

    # custom fields
    for field in custom_headers:
        if value_in_row(row, field):
            lead['custom'][field] = value_in_row(row, field)

    # address
    address = {}
    if value_in_row(row, 'address'):
        address['address'] = value_in_row(row, 'address')
    elif value_in_row(row, 'address_1') or value_in_row(row, 'address_2'):
        address['address'] = ('%s %s' % (value_in_row(row, 'address_1'), value_in_row(row, 'address_2'))).strip()
    if value_in_row(row, 'city'):
        address['city'] = title_case(value_in_row(row, 'city'))
    if value_in_row(row, 'state'):
        address['state'] = value_in_row(row, 'state')
    if value_in_row(row, 'zip'):
        address['zipcode'] = value_in_row(row, 'zip')
    if value_in_row(row, 'country'):
        address['country'] = value_in_row(row, 'country')
    if len(address):
        lead['addresses'] = [address]

    # contact
    contact = {}
    if value_in_row(row, 'contact'):
        contact['name'] = uncamel(value_in_row(row, 'contact'))
    if value_in_row(row, 'title'):
        contact['title'] = value_in_row(row, 'title')

    phones = []
    if value_in_row(row, 'phone'):
        phones.append({
            'phone': value_in_row(row, 'phone'),
            'type': 'office'
        })
    if value_in_row(row, 'mobile_phone'):
        phones.append({
            'phone': value_in_row(row, 'mobile_phone'),
            'type': 'mobile'
        })
    if value_in_row(row, 'fax'):
        phones.append({
            'phone': value_in_row(row, 'fax'),
            'type': 'fax'
        })
    if len(phones):
        contact['phones'] = phones

    emails = []
    if value_in_row(row, 'email'):
        emails.append({
            'email': value_in_row(row, 'email'),
            'type': 'office'
        })
    if len(emails):
        contact['emails'] = emails

    if len(contact):
        lead['contacts'] = [contact]

    return lead


# Create leads, grouped by company name
unique_leads = {}
for i, row in enumerate(reader):
    lead = lead_from_row(row)
    if not lead:
        continue

    if args.no_grouping:
        grouper = 'row-num-%s' % i
    else:
        # group by lead Name (company) if possible, otherwise put each row in its own lead
        grouper = lead['name'] if lead['name'] else ('row-num-%s' % i)

    if grouper not in unique_leads:
        unique_leads[grouper] = lead
    elif lead['contacts'] not in unique_leads[grouper]['contacts']:
        unique_leads[grouper]['contacts'].extend(lead['contacts'])

print 'Found %d leads (grouped by company) from %d contacts.' % (len(unique_leads), import_count)

print '\nHere is a sample lead (last row):'
print json.dumps(unique_leads[grouper], indent=4)

if raw_input('\nAre you sure you want to continue? (y/n) ') != 'y':
    sys.exit()

##############################################################################

api = CloseIO_API(args.api_key, development=args.development)

progress_widgets = ['Importing %d rows: ' % import_count, Percentage(), ' ', Bar(), ' ', ETA(), ' ', FileTransferSpeed()]
pbar = ProgressBar(widgets=progress_widgets, maxval=import_count).start()

dupes_cnt = 0

for key, val in unique_leads.items():
    retries = 5

    # check if it's a duplicate
    dupe = False
    if args.skip_duplicates and val.get('name'):

        # get the org id necessary for search
        org_id = api.get('api_key')['data'][0]['organization_id']

        # get all the search results for given lead name
        search_results = []
        filters = {
            'organization_id': org_id,
            'query': 'name:"%s"' % key,
        }
        skip = 0
        limit = 100
        while True:
            filters['_skip'] = skip
            filters['_limit'] = skip + limit
            results = api.get('lead', data=filters)['data']
            search_results.extend(results)
            if len(results) < limit:
                break
            skip += limit
        for result in search_results:
            if result['display_name'] == val['name']:
                dupe = True
                break

    while retries > 0:
        if dupe:
            dupes_cnt += 1
            print 'Duplicate - not importing: %s' % val['name']
            break

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
if args.skip_duplicates:
    print 'Duplicates: %d' % dupes_cnt

