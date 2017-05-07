import json

import pytest
import responses

from closeio_api import Client, APIError


@pytest.fixture
def api_client():
    return Client('fake-api-key')


@responses.activate
def test_list_leads(api_client):
    responses.add(
        responses.GET,
        'https://app.close.io/api/v1/lead/',
        body=json.dumps({
            'has_more': False,
            'data': [
                {
                    'name': 'Sample Lead',
                    'contacts': [],
                    # Other lead fields omitted for brevity
                }
            ]
        }),
        status=200,
        content_type='application/json'
    )

    resp = api_client.get('lead')
    assert not resp['has_more']
    assert resp['data'][0]['name'] == 'Sample Lead'

@responses.activate
def test_fetch_lead(api_client):
    responses.add(
        responses.GET,
        'https://app.close.io/api/v1/lead/lead_abcdefghijklmnop/',
        body=json.dumps({
            'name': 'Sample Lead',
            'contacts': [],
            # Other lead fields omitted for brevity
        }),
        status=200,
        content_type='application/json'
    )

    resp = api_client.get('lead/lead_abcdefghijklmnop')
    assert resp['name'] == 'Sample Lead'

@responses.activate
def test_create_lead(api_client):
    def request_callback(request):
        payload = json.loads(request.body)
        expected_payload = {'name': 'Sample Lead'}
        assert payload == expected_payload
        return (200, {}, json.dumps(payload))

    responses.add_callback(
        responses.POST,
        'https://app.close.io/api/v1/lead/',
        callback=request_callback,
        content_type='application/json',
    )

    resp = api_client.post('lead', {'name': 'Sample Lead'})
    assert resp['name'] == 'Sample Lead'

@responses.activate
def test_failed_create_lead(api_client):
    responses.add(
        responses.POST,
        'https://app.close.io/api/v1/lead/',
        body='Forbidden',
        status=403,
        content_type='application/json'
    )

    with pytest.raises(APIError):
        resp = api_client.post('lead', {'name': 'Sample Lead'})

@responses.activate
def test_search_for_leads(api_client):
    responses.add(
        responses.GET,
        'https://app.close.io/api/v1/lead/',
        body=json.dumps({
            'has_more': False,
            'data': [
                {
                    'name': 'Sample Lead',
                    'contacts': [],
                    # Other lead fields omitted for brevity
                }
            ]
        }),
        status=200,
        content_type='application/json'
    )
    def request_callback(request):
        args = json.loads(request.args)
        expected_args = {'query': 'name:sample'}
        assert args == expected_args
        return (200, {}, json.dumps({
            'has_more': False,
            'data': [
                {
                    'name': 'Sample Lead',
                    'contacts': [],
                    # Other lead fields omitted for brevity
                }
            ]
        }))

    responses.add_callback(
        responses.GET,
        'https://app.close.io/api/v1/lead/',
        callback=request_callback,
        content_type='application/json',
    )

    resp = api_client.get('lead', params={'query': 'name:sample'})
    assert not resp['has_more']
    assert resp['data'][0]['name'] == 'Sample Lead'

@responses.activate
def test_retry_on_rate_limit(api_client):

    with responses.RequestsMock() as rsps:

        # Rate limit the first request, suggesting that it can be retried in 1s.
        rsps.add(
            responses.GET,
            'https://app.close.io/api/v1/lead/lead_abcdefghijklmnop/',
            body=json.dumps({
                "error": {
                    "rate_reset": 1,
                    "message": "API call count exceeded for this 15 second window",
                    "rate_limit": 600,
                    "rate_window": 15
                }
            }),
            status=429,
            content_type='application/json'
        )

        # Respond correctly to the second request.
        rsps.add(
            responses.GET,
            'https://app.close.io/api/v1/lead/lead_abcdefghijklmnop/',
            body=json.dumps({
                'name': 'Sample Lead',
                'contacts': [],
                # Other lead fields omitted for brevity
            }),
            status=200,
            content_type='application/json'
        )

        resp = api_client.get('lead/lead_abcdefghijklmnop')
        assert resp['name'] == 'Sample Lead'

        # Make sure two calls were made to the API (one rate limited and one
        # successful).
        assert len(rsps.calls) == 2
