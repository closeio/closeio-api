import json
import time

import requests

from closeio_api.utils import local_tz_offset


# Max number of requests that can be executed concurrently in a single batch.
# This limit is used in API#map.
MAX_CONCURRENT_REQUESTS = 10


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

    def __init__(self, base_url, api_key=None, tz_offset=None,
                 async=False, max_retries=5, verify=True):
        assert base_url
        self.base_url = base_url
        self.async = async
        self.max_retries = max_retries
        self.tz_offset = tz_offset or str(local_tz_offset())
        self.verify = verify

        if async:
            # imported inline so that it is not a mandatory dependency
            import grequests
            self.requests = grequests
        else:
            self.requests = requests

        self.session = self.requests.Session()
        if api_key:
            self.session.auth = (api_key, '')
        self.session.headers.update({'Content-Type': 'application/json', 'X-TZ-Offset': self.tz_offset})

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

        full_url = self.base_url + endpoint

        if self.async:
            prepped_request = self.requests.AsyncRequest(method_name, full_url,
                                                         session=self.session,
                                                         verify=self.verify,
                                                         **kwargs)
        else:
            request = self.requests.Request(method_name, full_url, **kwargs)
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
        assert not self.async  # this method is always synchronous

        prepped_req = self._prepare_request(method_name, endpoint, api_key,
                                            data, debug, **kwargs)
        for retry_count in range(self.max_retries):
            try:
                response = self.session.send(prepped_req, verify=self.verify)
            except requests.exceptions.ConnectionError:
                if (retry_count + 1 == self.max_retries):
                    raise
                time.sleep(2)
            else:
                break

        if response.ok:
            return response.json()
        elif response.status_code == 400:
            raise ValidationError(response)
        else:
            raise APIError(response)

    def get(self, endpoint, params=None, **kwargs):
        """Send (sync client) or prepare (async client) a GET request
        to a given endpoint, for example:

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
        func = self._prepare_request if self.async else self._dispatch
        return func('get', endpoint+'/', **kwargs)

    def post(self, endpoint, data, **kwargs):
        """Send (sync client) or prepare (async client) a POST request
        to a given endpoint, for example:

        >>> api.post('lead', {'name': 'Brand New Lead'})
        {
            'name': 'Brand New Lead'
            # ... rest of the response omitted for brevity
        }
        """
        kwargs.update({'data': data})
        func = self._prepare_request if self.async else self._dispatch
        return func('post', endpoint+'/', **kwargs)

    def put(self, endpoint, data, **kwargs):
        """Send (sync client) or prepare (async client) a PUT request to
        a given endpoint, for example:

        >>> api.put('lead/SOME_LEAD_ID', {'name': 'New Name'})
        {
            'name': 'New Name'
            # ... rest of the response omitted for brevity
        }
        """
        kwargs.update({'data': data})
        func = self._prepare_request if self.async else self._dispatch
        return func('put', endpoint+'/', **kwargs)

    def delete(self, endpoint, **kwargs):
        """Send (sync client) or prepare (async client) a DELETE request
        to a given endpoint, for example:

        >>> api.delete('lead/SOME_LEAD_ID')
        {}
        """
        func = self._prepare_request if self.async else self._dispatch
        return func('delete', endpoint+'/', **kwargs)

    # Only for async requests
    def map(self, reqs, max_retries=None):
        """Execute a batch of asynchronous requests concurrently. For
        example:

        >>> reqs = []
        >>> reqs.append(api.post('lead', {'name': 'New Lead'}))
        >>> reqs.append(api.post('lead', {'name': 'Another New Lead'}))
        >>> api.map(reqs)
        [
            # list of dicts containing successful API responses and APIError
            # objects for failed requests.
        ]
        """
        if not self.async:
            raise NotImplementedError('map can only be used in an async Client')

        if len(reqs) > MAX_CONCURRENT_REQUESTS:
            raise ValueError(
                'Too many concurrent requests ({}). You can send up to {} in '
                'a single batch.'.format(len(reqs), MAX_CONCURRENT_REQUESTS)
            )

        if max_retries is None:
            max_retries = self.max_retries

        # TODO
        # There is no good way of catching or dealing with exceptions that are
        # raised during the request sending process when using map or imap.
        # When this issue is closed:
        # https://github.com/kennethreitz/grequests/pull/15
        # modify this method to repeat only the requests that failed because of
        # connection errors

        responses = [(
            response.json() if response.ok else APIError(response)
        ) for response in self.requests.map(reqs)]

        # retry the api calls that failed until they succeed or the
        # max_retries limit is reached
        retries = 0
        while True and retries < max_retries:
            n_errors = sum([int(isinstance(response, APIError))
                            for response in responses])
            if not n_errors:
                break

            # sleep 2 seconds before retrying requests
            time.sleep(2)

            error_ids = [i for i, resp in enumerate(responses)
                         if isinstance(responses[i], APIError)]
            new_reqs = [reqs[i] for i in range(len(responses))
                        if i in error_ids]

            new_resps = [(
                response.json() if response.ok else APIError(response)
            ) for response in self.requests.map(new_reqs)]

            # update the responses that previously finished with errors
            for i in range(len(error_ids)):
                responses[error_ids[i]] = new_resps[i]

            retries += 1

        return responses

    def _print_request(self, req):
        """Print a human-readable representation of a request."""
        if self.async:
            print(
                "Cannot print the request in async mode, because it isn't "
                "fully built until it's being sent."
            )
            return

        print('{}\n{}\n{}\n\n{}\n{}'.format(
            '----------- HTTP Request -----------',
            req.method + ' ' + req.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body or '',
            '----------- /HTTP Request -----------'))


class Client(API):
    def __init__(self, api_key=None, tz_offset=None, async=False,
                 max_retries=5, development=False):
        if development:
            base_url = 'https://local.close.io:5001/api/v1/'
            # See https://github.com/kennethreitz/requests/issues/2966
            verify = False
        else:
            base_url = 'https://app.close.io/api/v1/'
            verify = True
        super(Client, self).__init__(base_url, api_key, tz_offset=tz_offset,
                                     async=async, max_retries=max_retries,
                                     verify=verify)

