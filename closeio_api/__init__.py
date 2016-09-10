#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import requests
from closeio_api.utils import local_tz_offset


class APIError(Exception):
    def __init__(self, response):
        # For compatibility purposes we can access the original string through
        # the args property.
        super(APIError, self).__init__(response.text)
        self.response = response

class ValidationError(APIError):
    def __init__(self, response):
        super(ValidationError, self).__init__(response)

        # Easy access to errors.
        data = response.json()
        self.errors = data.get('errors', [])
        self.field_errors = data.get('field-errors', {})

class API(object):
    def __init__(self, base_url, api_key=None, tz_offset=None,
                 async=False, max_retries=5, verify=True):
        assert base_url
        self.base_url = base_url
        self.async = async
        self.max_retries = max_retries
        self.tz_offset = tz_offset or str(local_tz_offset())
        self.verify = verify

        if async:
            import grequests
            self.requests = grequests
        else:
            self.requests = requests

        self.session = self.requests.Session()
        if api_key:
            self.session.auth = (api_key, '')
        self.session.headers.update({'Content-Type': 'application/json', 'X-TZ-Offset': self.tz_offset})

    def _print_request(self, request):
        print('{}\n{}\n{}\n\n{}\n{}'.format(
            '----------- HTTP Request -----------',
            request.method + ' ' + request.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in request.headers.items()),
            request.body or '',
            '----------- /HTTP Request -----------'))

    def dispatch(self, method_name, endpoint, **kwargs):
        api_key = kwargs.pop('api_key', None)
        data = kwargs.pop('data', None)
        debug = kwargs.pop('debug', False)

        for retry_count in range(self.max_retries):
            try:
                if api_key:
                    auth = (api_key, '')
                else:
                    auth = None
                    assert self.session.auth, 'Must specify api_key.'
                kwargs.update({
                    'auth': auth,
                    'json': data
                })
                request = requests.Request(
                    method_name,
                    self.base_url+endpoint,
                    **kwargs
                )
                prepped_request = self.session.prepare_request(request)
                if debug:
                    self._print_request(prepped_request)
                response = self.session.send(prepped_request,
                                             verify=self.verify)
            except requests.exceptions.ConnectionError:
                if (retry_count + 1 == self.max_retries):
                    raise
                time.sleep(2)
            else:
                break

        if self.async:
            return response
        else:
            if response.ok:
                return response.json()
            elif response.status_code == 400:
                raise ValidationError(response)
            else:
                raise APIError(response)

    def get(self, endpoint, params=None, **kwargs):
        kwargs.update({'params': params})
        return self.dispatch('get', endpoint, **kwargs)

    def post(self, endpoint, data, **kwargs):
        kwargs.update({'data': data})
        return self.dispatch('post', endpoint+'/', **kwargs)

    def put(self, endpoint, data, **kwargs):
        kwargs.update({'data': data})
        return self.dispatch('put', endpoint+'/', **kwargs)

    def delete(self, endpoint, **kwargs):
        return self.dispatch('delete', endpoint+'/', **kwargs)

    # Only for async requests
    def map(self, reqs, max_retries=None):
        if max_retries is None:
            max_retries = self.max_retries
        # TODO
        # There is no good way of catching or dealing with exceptions that are
        # raised during the request sending process when using map or imap.
        # When this issue is closed:
        # https://github.com/kennethreitz/grequests/pull/15
        # modify this method to repeat only the requests that failed because of
        # connection errors
        if self.async:
            import grequests
            responses = [(
                response.json() if response.ok else APIError(response)
            ) for response in grequests.map(reqs)]
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
                ) for response in grequests.map(new_reqs)]
                # update the responses that previously finished with errors
                for i in range(len(error_ids)):
                    responses[error_ids[i]] = new_resps[i]
                retries += 1
            return responses


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
