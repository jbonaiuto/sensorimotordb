import sys
import django
import os
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")
from tastypie.test import TestApiClient

def test_api(username, password):
    api_client = TestApiClient()
    result = api_client.client.login(username=username, password=password)
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/visuomotor_classification_analysis_results/?analysis__experiment=73', format='json'))
    start = time.time()
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/full_recording_trial/?condition__in=432,433,437,438,442,443,434,439,444,430,435,440,431,436,441&limit=0', format='json'))
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/full_recording_trial/?unit_recordings__unit=518&limit=0', format='json'))
    print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/event/?trial__condition__experiment=108', format='json'))
    end = time.time()
    print(end - start)
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/visuomotor_classification_analysis/1/', format='json'))
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/analysis/1/', format='json'))
    #print(api_client.get('http://localhost:8000/sensorimotordb/api/v1/unit_classification/1/', format='json'))


if __name__=='__main__':
    django.setup()
    test_api(sys.argv[1],sys.argv[2])