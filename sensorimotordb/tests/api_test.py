import sys
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")
from tastypie.test import TestApiClient

def test_api(username, password):
    api_client = TestApiClient()
    result = api_client.client.login(username=username, password=password)
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/visuomotor_classification_analysis_results/?analysis__experiment=73', format='json'))
    print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/visuomotor_classification_analysis_results/5/', format='json'))
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/visuomotor_classification_analysis/1/', format='json'))
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/analysis/1/', format='json'))
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/unit_classification/1/', format='json'))


if __name__=='__main__':
    django.setup()
    test_api(sys.argv[1],sys.argv[2])