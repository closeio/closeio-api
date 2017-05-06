import logging
import time

import requests

from closeio_api.utils import local_tz_offset


DEFAULT_RATE_LIMIT_DELAY = 2   # Seconds


class APIError(Exception):
    """Raised when sending a request to the API failed."""

    def __init__(self, response):
        # For compatibility purposes we can access the original string through
        # the args property.
        super(APIError, self).__init__(response.text)
        self.response = response


class ValidationError(APIError):
    """Raised when the API returns validation errors."""

    def __init__(self, response):
        super(ValidationError, self).__init__(response)

        # Easy access to errors.
        data = response.json()
        self.errors = data.get('errors', [])
        self.field_errors = data.get('field-errors', {})


class API(object):
    """Main class interacting with the Close.io API."""

    def __init__(self, base_url, api_key=None, tz_offset=None, max_retries=5,
                 verify=True):
        assert base_url
        self.base_url = base_url
        self.max_retries = max_retries
        self.tz_offset = tz_offset or str(local_tz_offset())
        self.verify = verify

        self.session = requests.Session()
        if api_key:
            self.session.auth = (api_key, '')

        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-TZ-Offset': self.tz_offset
        })

    def _prepare_request(self, method_name, endpoint, api_key=None, data=None,
                         debug=False, **kwargs):
        """Construct and return a requests.Request object based on
        provided parameters.
        """
        if api_key:
            auth = (api_key, '')
        else:
            auth = None
            assert self.session.auth, 'Must specify api_key.'

        kwargs.update({
            'auth': auth,
            'json': data
        })
        request = requests.Request(method_name, self.base_url + endpoint,
                                   **kwargs)
        prepped_request = self.session.prepare_request(request)

        if debug:
            self._print_request(prepped_request)

        return prepped_request

    def _dispatch(self, method_name, endpoint, api_key=None, data=None,
                  debug=False, **kwargs):
        """Prepare and send a request with given parameters. Return a
        dict containing the response data or raise an exception if any
        errors occured.
        """
        prepped_req = self._prepare_request(method_name, endpoint, api_key,
                                            data, debug, **kwargs)

        for retry_count in range(self.max_retries):
            try:
                response = self.session.send(prepped_req, verify=self.verify)
            except requests.exceptions.ConnectionError:
                if retry_count + 1 == self.max_retries:
                    raise
                time.sleep(2)
            else:
                # Check if request was rate limited.
                if response.status_code == 429:
                    sleep_time = self._get_rate_limit_sleep_time(response)
                    logging.debug('Request was rate limited, sleeping %d seconds', sleep_time)
                    time.sleep(sleep_time)
                    continue

                # Break out of the retry loop if the request was successful.
                break

        if response.ok:
            return response.json()
        elif response.status_code == 400:
            raise ValidationError(response)
        else:
            raise APIError(response)

    def _get_rate_limit_sleep_time(self, response):
        """Get rate limit window expiration time from response."""
        try:
            data = response.json()
            return float(data['error']['rate_reset'])
        except (AttributeError, KeyError, ValueError):
            logging.exception('Error parsing rate limiting response')
            return DEFAULT_RATE_LIMIT_DELAY

    def get(self, endpoint, params=None, **kwargs):
        """Send a GET request to a given endpoint, for example:

        >>> api.get('lead', {'query': 'status:"Potential"'})
        {
            'has_more': False,
            'total_results': 5,
            'data': [
                # ... list of leads in "Potential" status
            ]
        }
        """
        kwargs.update({'params': params})
        return self._dispatch('get', endpoint+'/', **kwargs)

    def post(self, endpoint, data, **kwargs):
        """Send a POST request to a given endpoint, for example:

        >>> api.post('lead', {'name': 'Brand New Lead'})
        {
            'name': 'Brand New Lead'
            # ... rest of the response omitted for brevity
        }
        """
        kwargs.update({'data': data})
        return self._dispatch('post', endpoint+'/', **kwargs)

    def put(self, endpoint, data, **kwargs):
        """Send a PUT request to a given endpoint, for example:

        >>> api.put('lead/SOME_LEAD_ID', {'name': 'New Name'})
        {
            'name': 'New Name'
            # ... rest of the response omitted for brevity
        }
        """
        kwargs.update({'data': data})
        return self._dispatch('put', endpoint+'/', **kwargs)

    def delete(self, endpoint, **kwargs):
        """Send a DELETE request to a given endpoint, for example:

        >>> api.delete('lead/SOME_LEAD_ID')
        {}
        """
        return self._dispatch('delete', endpoint+'/', **kwargs)

    def _print_request(self, req):
        """Print a human-readable representation of a request."""
        print('{}\n{}\n{}\n\n{}\n{}'.format(
            '----------- HTTP Request -----------',
            req.method + ' ' + req.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body or '',
            '----------- /HTTP Request -----------'
        ))


class Client(API):
    def __init__(self, api_key=None, tz_offset=None, max_retries=5,
                 development=False):
        if development:
            base_url = 'https://local.close.io:5001/api/v1/'
            # See https://github.com/kennethreitz/requests/issues/2966
            verify = False
        else:
            base_url = 'https://app.close.io/api/v1/'
            verify = True
        super(Client, self).__init__(base_url, api_key, tz_offset=tz_offset,
                                     max_retries=max_retries, verify=verify)

