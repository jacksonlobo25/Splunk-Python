# Common/splunk_logger.py
import requests
import json
import time
import logging

# Splunk Config
SPLUNK_HEC_URL = 'http://34.41.226.221:8088/services/collector'
SPLUNK_TOKEN = '16e22809-f1a7-4972-b91d-b724a7cfb02b'

# Setup stdout logger (Dynatrace reads this)
stdout_logger = logging.getLogger("stdout_logger")
if not stdout_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    stdout_logger.addHandler(handler)
    stdout_logger.setLevel(logging.INFO)

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
        # ✅ Log to Splunk
        response = requests.post(SPLUNK_HEC_URL, headers=headers, data=json.dumps(payload), verify=False)
        if response.status_code != 200:
            stdout_logger.error(f"Splunk log failed: {response.status_code} {response.text}")

        # ✅ Also log to stdout (for Dynatrace)
        stdout_logger.info(json.dumps(event))

    except Exception as e:
        stdout_logger.error(f"Splunk logging error: {e}")
