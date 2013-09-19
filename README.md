## Close.io API

A convenient Python wrapper for the [Close.io](https://close.io/) API.

See the developer docs at http://developer.close.io. For any questions or issues, please contact support(at)close(dot)io.

### Sample Usage
```
from client.api import CloseIO_API

api = CloseIO_API('YOUR_API_KEY')

# post a lead
lead = api.post('lead', data={'name': 'New Lead'})

# get 5 most recently updated opportunities
opportunities = api.get('opportunity', data={'_order_by': '-date_updated', '_limit': 5})
```

Check out `scripts/` for more detailed examples.

### Other Languages

Thanks to our awesome users, other languages are supported, too:
* Ruby: https://github.com/taylorbrooks/closeio
* PHP: https://github.com/TheDeveloper/closeio-php-sdk
* Node.js: https://github.com/wehriam/Close.io
