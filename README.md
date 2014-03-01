## Close.io API

A convenient Python wrapper for the [Close.io](https://close.io/) API.

See the developer docs at http://developer.close.io. For any questions or issues, please contact support(at)close(dot)io.

### Sample Usage
```
from closeio_api import Client
import urllib

api = Client('YOUR_API_KEY')

# post a lead
lead = api.post('lead', data={'name': 'New Lead'})

# get 5 most recently updated opportunities
opportunities = api.get('opportunity', data={'_order_by': '-date_updated', '_limit': 5})

# fetch multiple leads (using search syntax)
lead_results = api.get('lead', data={
    '_limit': 10,
    '_fields': 'id,display_name,status_label',
    'query': 'custom.my_custom_field:"some_value" status:"Potential" sort:updated'
})

```

Check out `scripts/` for more detailed examples.

### Other Languages

Thanks to our awesome users, other languages are supported, too:
* Ruby: https://github.com/rest-client/rest-client or https://github.com/taylorbrooks/closeio
* PHP: [simple example](https://gist.github.com/philfreo/5406540) or https://github.com/TheDeveloper/closeio-php-sdk
* Node.js: https://github.com/wehriam/Close.io
