from tastypie.test import TestApiClient

def test_api(username, password):
    api_client = TestApiClient()
    result = api_client.client.login(username=username, password=password)
    print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/experiment/57/', format='json'))
