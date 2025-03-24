# Common/splunk_logger.py
import requests
import json
import time

SPLUNK_HEC_URL = 'http://35.226.42.206:8088/services/collector'
SPLUNK_TOKEN = '16e22809-f1a7-4972-b91d-b724a7cfb02b'

def log_to_splunk(event, sourcetype='web-app', index='main', host='flask-app'):
    headers = {
        'Authorization': f'Splunk {SPLUNK_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        'event': event,
        'sourcetype': sourcetype,
        'index': index,
        'host': host,
        'time': time.time()
    }

    try:
        response = requests.post(SPLUNK_HEC_URL, headers=headers, data=json.dumps(payload), verify=False)
        if response.status_code != 200:
            print(f"Splunk log failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Splunk logging error: {e}")
