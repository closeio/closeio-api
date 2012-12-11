In this directory you'll find some Python scripts to help with interacting with the [Close.io](http://close.io/) API.

Install basic dependencies
-----
Before you start, you should already have `git`, `python-2.7` and `virtualenv` installed. For OS X users, we recommend [MacPorts](http://www.macports.org/).

Setup
-----
1. `git clone git@github.com:elasticsales/closeio-api.git`
1. `cd closeio-api/scripts`
1. `virtualenv-2.7 --distribute venv`
1. `. venv/bin/activate`
1. `pip install -U -r requirements.txt`

How to run the CSV importing script
-----
1. Make sure your CSV has all of these columns, _in this order_: 

```
company_name
url
status
email
phone
contact_name
contact_title
address
city
state (2 letter abbreviation)
zip
country (2 letter abbreviation)
(any additional fields will be added as custom fields)
```
All fields are optional (can be blank), but you must have all of these columns.

2. Make sure (if you haven't already in step 1) you're in the `closeio-api/scripts` directory and you have activated your virtual environment by running `. venv/bin/activate`.

3. Run the import script: `./csv_to_cio.py --api_key YOUR_API_KEY_HERE ~/path/to/your/leads.csv

