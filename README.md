## Close.io API

A convenient Python wrapper for the [Close.io](https://close.io/) API.

See the developer docs at http://developer.close.io. For any questions or issues, please contact support(at)close(dot)io.

### Sample Usage

```python
from closeio_api import Client
import urllib

api = Client('YOUR_API_KEY')

# post a lead
lead = api.post('lead', data={'name': 'New Lead'})

# get 5 most recently updated opportunities
opportunities = api.get('opportunity', params={'_order_by': '-date_updated', '_limit': 5})

# fetch multiple leads (using search syntax)
lead_results = api.get('lead', params={
    '_limit': 10,
    '_fields': 'id,display_name,status_label',
    'query': 'custom.my_custom_field:"some_value" status:"Potential" sort:updated'
})
```

Check out `scripts/` for more detailed examples.

### Running a script
```bash
$ git clone https://github.com/closeio/closeio-api.git
$ cd closeio-api
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python setup.py install
$ python scripts/merge_leads.py -k MYAPIKEY 
...

```

### Other Languages

Thanks to our awesome users, other languages are supported, too:
* Ruby: [simple example](https://gist.github.com/philfreo/9359930) that uses [RestClient](https://github.com/rest-client/rest-client), or use [taylorbrook's gem](https://github.com/taylorbrooks/closeio)
* PHP: [simple example](https://gist.github.com/philfreo/5406540) or https://github.com/loopline-systems/closeio-api-wrapper or https://github.com/TheDeveloper/closeio-php-sdk
* Node.js: https://github.com/closeio/closeio-node
* C#: https://github.com/MoreThanRewards/CloseIoDotNet
