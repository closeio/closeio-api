# Close.io API

This page describes how developers can use the API for [Close.io](https://close.io/). For any questions or issues, please contact engineering(at)elasticsales(dot)com.

## Authentication
HTTP Basic authentication. The API key acts as the username. API keys are per-organization and can be generated and deleted in the Settings page.

**Curl**
```shell
curl -XPOST "https://app.close.io/api/v1/lead/" -d '{"name":"test lead"}' -u yourapikey:
#notice the ':' at the end of the api key.  this is used because the key is sent as the username with a blank password.
```

**Python**
```python
import requests, json, base64

api_key = 'yourapikey'
data = {'name': 'test lead'}
url = 'https://app.close.io/api/v1/lead/'

response = requests.post(url, data=json.dumps(data), auth=(api_key, ''), headers={'Content-Type': 'application/json'})

print response, response.text
```

## Endpoints

### Me
Fetch. 
Provides user-specific information for the currently logged in user (of the apikey provided).

**Curl**
```shell
curl -XGET "https://app.close.io/api/v1/me/" -u yourapikey:
```
**Python**
```python
response = requests.get('https://app.close.io/api/v1/me/', auth=(api_key, ''))
print response.json
```

```
{
    "id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS",
    "organizations": [
        {
            "id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ",
            "name": "My Organization"
        }
    ],
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@example.com"
}
```

### Opportunity
Definition
```python
class Opportunity(DocumentBase, RandomPKDocument):
    organization = ReferenceField(Organization)
    lead = ReferenceField(Lead, required=True)
    user = ReferenceField(User)

    status = StringField(choices=OpportunityStatus.choices(), default=OpportunityStatus.Active)
    value = IntField(min_value=0) # in cents
    value_period = StringField(choices=OpportunityValuePeriod.choices(), default=OpportunityValuePeriod.OneTime)
    confidence = IntField(default=50, min_value=0, max_value=100)
    date_won = DateTimeField() # date only
    note = TrimmedStringField()
```
### Lead
Definition
```python
class Lead(DocumentBase, RandomPKDocument):
    organization = ReferenceField(Organization, required=True)

    name = TrimmedStringField()
    description = TrimmedStringField()
    status = TrimmedStringField()
    custom = DictField()
    addresses = ListField(EmbeddedDocumentField(Address))
    contacts = ListField(ReferenceField(Contact))
```
Fetch
**Curl**
```shell
curl -XGET "https://app.close.io/api/v1/lead/lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh/" -u yourapikey:

{"status": "qualified", "activities": [{"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:57:52.851000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:56:22.718000+00:00", "duration": 65, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_MQtG6KJJ9wwop9ixNtLINqzT46CVmbnY3VpNA9BG6RI"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:56:01.069000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:55:12.270000+00:00", "duration": 35, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_1oMsP9eGpaSlcVwX3xCyPObmuLSKwOQm2XiqZ6fyoE1"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:37:55.430000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:36:40.984000+00:00", "duration": 63, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_869XaRfZkljGdacJIENigpi6hmGEGfjs6X7T0KU38G8"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:35:18.808000+00:00", "voicemail_duration": null, "direction": null, "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:35:18.808000+00:00", "duration": null, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_xTWAOammOu8SaBdRN3HxoxcIdBY01zfMz60nwuPU0yH"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T22:52:28.057000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": null, "note": "these are call notes.", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T22:52:08.459000+00:00", "duration": 0, "user_id": null, "id": "acti_rK2JDcDiZQDjkRCY63Ck8H8tnomlt1Ete9i8ArEI2L7"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T22:29:44.282000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": null, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T22:29:34.292000+00:00", "duration": 0, "user_id": null, "id": "acti_cNURDO5QWYohJAlB7Fed5C6PYWnJ3lvgKc7CcRR9BHn"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T19:11:34.746000+00:00", "voicemail_duration": null, "direction": "inbound", "comments": [], "is_new": null, "note": null, "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T19:10:58.662000+00:00", "duration": 6, "user_id": null, "id": "acti_0j9WCoMHGkkFmmrWpRYK46PhuY5R0jfivSGqxCgBZDv"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T19:10:43.038000+00:00", "voicemail_duration": null, "direction": "inbound", "comments": [], "is_new": null, "note": null, "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T19:10:07.775000+00:00", "duration": 5, "user_id": null, "id": "acti_Y1MklJ6oQzuaOVkrsEPqDD3iUQ2ioeqWrPoKsFaaPB8"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T18:40:42.264000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": null, "note": "sure good deal", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T18:40:08.206000+00:00", "duration": 12, "user_id": null, "id": "acti_mK4NCTp4P7HhHUn2ZBsb2A6ze7bOyIpLkcv0t3UgyZE"}, {"_type": "Created", "user_id": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T18:40:00.028000+00:00", "is_new": null, "comments": [], "organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "source": null, "contact_id": null, "date_created": "2012-08-27T18:40:00.028000+00:00", "id": "acti_RxhrJLQnMvwIETPwWhxPGBsvZJnhZ8zs9jGETLdxx1m"}], "display_name": "anthony nemitz", "addresses": [], "name": "anthony nemitz", "contacts": [{"name": "", "title": "", "phones": [{"phone": "+17632225552", "phone_formatted": "+1 763-222-5552", "type": "office"}], "emails": [], "organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk"}], "date_updated": "2012-09-04T20:57:52.856000+00:00", "opportunities": [], "custom": {}, "organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "date_created": "2012-08-27T18:40:00.025000+00:00", "id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "description": ""}              
```
Update
**Curl**
```shell
curl -XPUT "https://app.close.io/api/v1/lead/lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh/" -d '{"name":"test"}' -u yourapikey: -H 'Content-Type: application/json'

{"status": "qualified", "activities": [{"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:57:52.851000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:56:22.718000+00:00", "duration": 65, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_MQtG6KJJ9wwop9ixNtLINqzT46CVmbnY3VpNA9BG6RI"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:56:01.069000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:55:12.270000+00:00", "duration": 35, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_1oMsP9eGpaSlcVwX3xCyPObmuLSKwOQm2XiqZ6fyoE1"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:37:55.430000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:36:40.984000+00:00", "duration": 63, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_869XaRfZkljGdacJIENigpi6hmGEGfjs6X7T0KU38G8"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-09-04T20:35:18.808000+00:00", "voicemail_duration": null, "direction": null, "comments": [], "is_new": false, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-09-04T20:35:18.808000+00:00", "duration": null, "user_id": "user_H7vK6LZMChjkOvvgsj08argnBiFeIpPmM6crmOMQ8rS", "id": "acti_xTWAOammOu8SaBdRN3HxoxcIdBY01zfMz60nwuPU0yH"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T22:52:28.057000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": null, "note": "these are call notes.", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T22:52:08.459000+00:00", "duration": 0, "user_id": null, "id": "acti_rK2JDcDiZQDjkRCY63Ck8H8tnomlt1Ete9i8ArEI2L7"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T22:29:44.282000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": null, "note": "", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T22:29:34.292000+00:00", "duration": 0, "user_id": null, "id": "acti_cNURDO5QWYohJAlB7Fed5C6PYWnJ3lvgKc7CcRR9BHn"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T19:11:34.746000+00:00", "voicemail_duration": null, "direction": "inbound", "comments": [], "is_new": null, "note": null, "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T19:10:58.662000+00:00", "duration": 6, "user_id": null, "id": "acti_0j9WCoMHGkkFmmrWpRYK46PhuY5R0jfivSGqxCgBZDv"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T19:10:43.038000+00:00", "voicemail_duration": null, "direction": "inbound", "comments": [], "is_new": null, "note": null, "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T19:10:07.775000+00:00", "duration": 5, "user_id": null, "id": "acti_Y1MklJ6oQzuaOVkrsEPqDD3iUQ2ioeqWrPoKsFaaPB8"}, {"organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "_type": "Call", "voicemail_url": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T18:40:42.264000+00:00", "voicemail_duration": null, "direction": "outbound", "comments": [], "is_new": null, "note": "sure good deal", "phone": "+17632225552", "contact_id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk", "date_created": "2012-08-27T18:40:08.206000+00:00", "duration": 12, "user_id": null, "id": "acti_mK4NCTp4P7HhHUn2ZBsb2A6ze7bOyIpLkcv0t3UgyZE"}, {"_type": "Created", "user_id": null, "lead_id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "date_updated": "2012-08-27T18:40:00.028000+00:00", "is_new": null, "comments": [], "organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "source": null, "contact_id": null, "date_created": "2012-08-27T18:40:00.028000+00:00", "id": "acti_RxhrJLQnMvwIETPwWhxPGBsvZJnhZ8zs9jGETLdxx1m"}], "display_name": "test", "addresses": [], "name": "test", "contacts": [{"name": "", "title": "", "phones": [{"phone": "+17632225552", "phone_formatted": "+1 763-222-5552", "type": "office"}], "emails": [], "organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "id": "cont_3uawb3nYN7EDC4EJWqpvrylfIJc8nHBkFQn7UQl16fk"}], "date_updated": "2012-09-14T06:00:36.884000+00:00", "opportunities": [], "custom": {}, "organization_id": "orga_NAOdGogArgYOLvYbsaLyLG9AbK8CscWiIIp2lD4LXbZ", "date_created": "2012-08-27T18:40:00.025000+00:00", "id": "lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh", "description": ""}
```
Create
**Curl**
```shell
curl -XPOST "https://app.close.io/api/v1/lead/" -d '{"name":"Nemitz Co", "contacts": [{"name":"Anthony Nemitz", "title":"CEO", "phones":[{"phone":"7632225552", "type":"mobile"}], "emails":[{"email": "anemitz@gmail.com","type":"home"}]}]}' -u yourapikey: -H 'Content-Type: application/json'

{"status": "", "activities": [{"_type": "Created", "user_id": "user_RsorOiSu4owQylr28yEylca5W8BJXIL5qWIRua4lNxN", "lead_id": "lead_0DvBcipgqfWkiso51mybHenrRVfFs96LC7VpO52LnGq", "date_updated": "2012-09-14T08:33:06.048000+00:00", "is_new": null, "comments": [], "organization_id": "orga_XbVPt5fFbKlYTz9PW5Ih0XDhViV10YihIaEfMEb6fVW", "source": "api", "contact_id": null, "date_created": "2012-09-14T08:33:06.048000+00:00", "id": "acti_ybvudNLKTLowcioYVoDHMT549X83ScuCFdielClkvUD"}], "display_name": "Nemitz Co", "addresses": [], "name": "Nemitz Co", "contacts": [{"name": "Anthony Nemitz", "title": "CEO", "phones": [{"phone": "+17632225552", "phone_formatted": "+1 763-222-5552", "type": "mobile"}], "emails": [{"type": "home", "email": "anemitz@gmail.com"}], "organization_id": "orga_XbVPt5fFbKlYTz9PW5Ih0XDhViV10YihIaEfMEb6fVW", "id": "cont_WwEWPguFumIpcQQIlqgKdjyMiGKu3ZRGf2Xb7RQxxSv"}], "date_updated": "2012-09-14T08:33:06.036000+00:00", "opportunities": [], "custom": {}, "organization_id": "orga_XbVPt5fFbKlYTz9PW5Ih0XDhViV10YihIaEfMEb6fVW", "date_created": "2012-09-14T08:33:06.036000+00:00", "id": "lead_0DvBcipgqfWkiso51mybHenrRVfFs96LC7VpO52LnGq", "description": ""}
```

Delete
**Curl**
```shell
curl -XDELETE "https://app.close.io/api/v1/lead/lead_5ISwLcsJWlr1ISL935eFoS2okRDIBun6klQCyR05Bnh/"
```

### Contact
Definitions
```python
class ContactPhone(EmbeddedDocument):
    type = TrimmedStringField()
    phone = PhoneField(required=True)

class ContactEmail(EmbeddedDocument):
    type = TrimmedStringField(required=True)
    email = EmailField(required=True)

class Contact(DocumentBase, RandomPKDocument):
    organization = ReferenceField(Organization)

    name = TrimmedStringField()
    title = TrimmedStringField()
    emails = ListField(EmbeddedDocumentField(ContactEmail))
    phones = ListField(EmbeddedDocumentField(ContactPhone))
```
### Activity
* Call
* Email
* Note