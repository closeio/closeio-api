import json

import pytest
import responses

from closeio_api import Client


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

