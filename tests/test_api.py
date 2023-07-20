import json

import pytest

import responses
from closeio_api import APIError, Client

SAMPLE_LEAD_RESPONSE = {
    'name': 'Sample Lead',
    'contacts': [],
    # Other lead fields omitted for brevity
}

SAMPLE_LEADS_RESPONSE = {
    'has_more': False,
    'data': [SAMPLE_LEAD_RESPONSE]
}


@pytest.fixture
def api_client():
    """Return the Close API client fixture."""
    return Client('fake-api-key')

@responses.activate
def test_list_leads(api_client):
    responses.add(
        responses.GET,
        'https://api.close.com/api/v1/lead/',
        body=json.dumps(SAMPLE_LEADS_RESPONSE),
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
        'https://api.close.com/api/v1/lead/lead_abcdefghijklmnop/',
        body=json.dumps(SAMPLE_LEAD_RESPONSE),
        status=200,
        content_type='application/json'
    )

    resp = api_client.get('lead/lead_abcdefghijklmnop')
    assert resp['name'] == 'Sample Lead'

@responses.activate
def test_create_lead(api_client):
    def request_callback(request):
        payload = json.loads(request.body.decode('UTF-8'))
        expected_payload = {'name': 'Sample Lead'}
        assert payload == expected_payload
        return (200, {}, json.dumps(payload))

    responses.add_callback(
        responses.POST,
        'https://api.close.com/api/v1/lead/',
        callback=request_callback,
        content_type='application/json',
    )

    resp = api_client.post('lead', {'name': 'Sample Lead'})
    assert resp['name'] == 'Sample Lead'

@responses.activate
def test_failed_create_lead(api_client):
    responses.add(
        responses.POST,
        'https://api.close.com/api/v1/lead/',
        body='Forbidden',
        status=403,
        content_type='application/json'
    )

    with pytest.raises(APIError):
        resp = api_client.post('lead', {'name': 'Sample Lead'})

@responses.activate
def test_search_for_leads(api_client):
    def request_callback(request):
        assert request.url == 'https://api.close.com/api/v1/lead/?query=name%3Asample'
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
        'https://api.close.com/api/v1/lead/',
        callback=request_callback,
        content_type='application/json',
    )

    resp = api_client.get('lead', params={'query': 'name:sample'})
    assert not resp['has_more']
    assert resp['data'][0]['name'] == 'Sample Lead'

@responses.activate
@pytest.mark.parametrize(
    "headers",
    [
        {"RateLimit-Reset": "1"},
        {"Retry-After": "1"},
        {"RateLimit": "limit=100, remaining=0, reset=1"},
        {
            "Retry-After": "1",
            "RateLimit-Reset": "1",
            "RateLimit": "limit=100, remaining=0, reset=1",
        },
    ]
)
def test_retry_on_rate_limit(api_client, headers):
    with responses.RequestsMock() as rsps:

        # Rate limit the first request and suggest it can be retried in 1 sec.
        rsps.add(
            responses.GET,
            'https://api.close.com/api/v1/lead/lead_abcdefghijklmnop/',
            body=json.dumps({}),
            status=429,
            content_type='application/json',
            headers=headers,
        )

        # Respond correctly to the second request.
        rsps.add(
            responses.GET,
            'https://api.close.com/api/v1/lead/lead_abcdefghijklmnop/',
            body=json.dumps(SAMPLE_LEAD_RESPONSE),
            status=200,
            content_type='application/json'
        )

        resp = api_client.get('lead/lead_abcdefghijklmnop')
        assert resp['name'] == 'Sample Lead'

        # Make sure two calls were made to the API (one rate limited and one
        # successful).
        assert len(rsps.calls) == 2

@responses.activate
def test_validation_error(api_client):
    responses.add(
        responses.POST,
        'https://api.close.com/api/v1/contact/',
        body=json.dumps({
            'errors': [],
            'field-errors': {
                'lead': 'This field is required.'
            }
        }),
        status=400,
        content_type='application/json'
    )

    with pytest.raises(APIError) as excinfo:
        api_client.post('contact', {'name': 'new lead'})

    err = excinfo.value
    assert err.errors == []
    assert err.field_errors['lead'] == 'This field is required.'

@responses.activate
def test_204_responses(api_client):
    responses.add(
        responses.DELETE,
        "https://api.close.com/api/v1/pipeline/pipe_1234/",
        status=204
    )
    resp = api_client.delete('pipeline/pipe_1234')
    assert resp == ''
