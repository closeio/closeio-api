import logging
import time

from random import uniform

import requests

from closeio_api.utils import local_tz_offset

DEFAULT_RATE_LIMIT_DELAY = 2   # Seconds

# To update the package version, change this variable. This variable is also
# read by setup.py when installing the package. 
__version__ = '1.3'

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
    """Main class interacting with the Close API."""

    def __init__(self, base_url, api_key=None, tz_offset=None, max_retries=5,
                 verify=True):
        assert base_url
        self.base_url = base_url
        self.max_retries = max_retries
        self.tz_offset = str(tz_offset or local_tz_offset())
        self.verify = verify

        self.session = requests.Session()
        if api_key:
            self.session.auth = (api_key, '')

        self.session.headers.update({
            'User-Agent': 'Close/{} python ({})'.format(
                __version__,
                requests.utils.default_user_agent()
            ),
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

        headers = kwargs.pop('headers', {})
        if data:
            headers.update({
                'Content-Type': 'application/json'
            })

        kwargs.update({
            'auth': auth,
            'headers': headers,
            'json': data
        })
        request = requests.Request(method_name, self.base_url + endpoint,
                                   **kwargs)
        prepped_request = self.session.prepare_request(request)

        if debug:
            self._print_request(prepped_request)

        return prepped_request

    def _dispatch(self, method_name, endpoint, api_key=None, data=None,
                  debug=False, timeout=None, **kwargs):
        """Prepare and send a request with given parameters. Return a
        dict containing the response data or raise an exception if any
        errors occurred.
        """
        prepped_req = self._prepare_request(method_name, endpoint, api_key,
                                            data, debug, **kwargs)

        for retry_count in range(self.max_retries):
            try:
                response = self.session.send(prepped_req, verify=self.verify, timeout=timeout)
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
                
                # Retry 503 errors or 502 or 504 erors on GET requests. 
                elif response.status_code == 503 or (
                    method_name == 'get' and response.status_code in (502, 504)
                ):
                    sleep_time = self._get_randomized_sleep_time_for_error(
                        response.status_code, retry_count
                    )
                    logging.debug(
                        'Request hit a {}, sleeping for {} seconds'.format(
                            response.status_code, sleep_time
                        )
                    )
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
        """Get rate limit window expiration time from response if the response
        status code is 429. 
        """
        try:
            data = response.json()
            return float(data['error']['rate_reset'])
        except (AttributeError, KeyError, ValueError):
            logging.exception('Error parsing rate limiting response')
            return DEFAULT_RATE_LIMIT_DELAY

    def _get_randomized_sleep_time_for_error(self, status_code, retries):
        """Get sleep time for a given status code before we can try the
        request again.
        
        Each time we retry, we want to increase the time before we try again. 
        """
        if status_code == 503:
            return uniform(2, 4) * (retries + 1)
        
        elif status_code in (502, 504):
            return uniform(60, 90) * (retries + 1)
        
        return DEFAULT_RATE_LIMIT_DELAY
        
    def get(self, endpoint, params=None, timeout=None, **kwargs):
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
        return self._dispatch('get', endpoint+'/', timeout=timeout, **kwargs)

    def post(self, endpoint, data, timeout=None, **kwargs):
        """Send a POST request to a given endpoint, for example:

        >>> api.post('lead', {'name': 'Brand New Lead'})
        {
            'name': 'Brand New Lead'
            # ... rest of the response omitted for brevity
        }
        """
        kwargs.update({'data': data})
        return self._dispatch('post', endpoint+'/', timeout=timeout, **kwargs)

    def put(self, endpoint, data, timeout=None, **kwargs):
        """Send a PUT request to a given endpoint, for example:

        >>> api.put('lead/SOME_LEAD_ID', {'name': 'New Name'})
        {
            'name': 'New Name'
            # ... rest of the response omitted for brevity
        }
        """
        kwargs.update({'data': data})
        return self._dispatch('put', endpoint+'/', timeout=timeout, **kwargs)

    def delete(self, endpoint, timeout=None, **kwargs):
        """Send a DELETE request to a given endpoint, for example:

        >>> api.delete('lead/SOME_LEAD_ID')
        {}
        """
        return self._dispatch('delete', endpoint+'/', timeout=timeout, **kwargs)

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
            base_url = 'https://local-api.close.com:5001/api/v1/'
            # See https://github.com/kennethreitz/requests/issues/2966
            verify = False
        else:
            base_url = 'https://api.close.com/api/v1/'
            verify = True
        super(Client, self).__init__(base_url, api_key, tz_offset=tz_offset,
                                     max_retries=max_retries, verify=verify)

