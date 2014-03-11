import json
import time
import urllib
import requests
from closeio_api.utils import local_tz_offset

class APIError(Exception):
    pass

class API(object):
    def __init__(self, base_url, api_key, tz_offset=None, async=False, max_retries=5):
        assert base_url
        self.base_url = base_url
        self.api_key = api_key
        self.async = async
        self.max_retries = max_retries
        if async:
            import grequests
            self.requests = grequests
        else:
            self.requests = requests.Session()
        self.tz_offset = tz_offset or local_tz_offset()

    def dispatch(self, method_name, endpoint, data=None):
        method = getattr(self.requests, method_name)

        retries = 0
        while True and retries < self.max_retries:
            try:
                response = method(
                    self.base_url+endpoint,
                    data=data != None and json.dumps(data),
                    auth=(self.api_key, ''),
                    headers={'Content-Type': 'application/json', 'X-TZ-Offset': self.tz_offset}
                )
                break
            except requests.exceptions.ConnectionError:
                time.sleep(2)
                retries += 1

        if self.async:
            return response
        else:
            if response.ok:
                return response.json()
            else:
                raise APIError(response.text)

    def get(self, endpoint, data=None):
        if data:
            for k, v in data.iteritems():
                data[k] = unicode(v).encode('utf-8')
            endpoint += '/?'+urllib.urlencode(data)
        else:
            endpoint += '/'
        return self.dispatch('get', endpoint)

    def post(self, endpoint, data):
        return self.dispatch('post', endpoint+'/', data)

    def put(self, endpoint, data):
        return self.dispatch('put', endpoint+'/', data)

    def delete(self, endpoint):
        return self.dispatch('delete', endpoint+'/')

    # Only for async requests
    def map(self, reqs, max_retries=None):
        if max_retries == None:
            max_retries = self.max_retries
        # TODO
        # There is no good way of catching or dealing with exceptions that are raised
        # during the request sending process when using map or imap.
        # When this issue is closed: https://github.com/kennethreitz/grequests/pull/15
        # modify this method to repeat only the requests that failed because of
        # connection errors
        if self.async:
            import grequests
            responses = [(
                response.json() if response.ok else APIError()
            ) for response in grequests.map(reqs)]
            # retry the api calls that failed until they succeed or the max_retries limit is reached
            retries = 0
            while True and retries < max_retries:
                n_errors = sum([int(isinstance(response, APIError)) for response in responses])
                if not n_errors:
                    break
                # sleep 2 seconds before retrying requests
                time.sleep(2)
                error_ids = [i for i, resp in enumerate(responses) if isinstance(responses[i], APIError)]
                new_reqs = [reqs[i] for i in range(len(responses)) if i in error_ids]
                new_resps = [(
                    response.json() if response.ok else APIError()
                ) for response in grequests.map(new_reqs)]
                # update the responses that previously finished with errors
                for i in range(len(error_ids)):
                    responses[error_ids[i]] = new_resps[i]
                retries += 1
            return responses


class Client(API):
    def __init__(self, api_key, tz_offset=None, async=False, development=False):
        if development:
            base_url = 'http://localhost:5001/api/v1/'
        else:
            base_url = 'https://app.close.io/api/v1/'
        super(Client, self).__init__(base_url, api_key, tz_offset=None, async=False)



