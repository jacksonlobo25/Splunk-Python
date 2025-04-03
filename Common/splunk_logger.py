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
stdout_logger.propagate = False

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
        response = requests.post(
            SPLUNK_HEC_URL,
            headers=headers,
            data=json.dumps(payload),
            verify=False
        )

        if response.status_code != 200:
            stdout_logger.error(f"[Splunk Error] HTTP {response.status_code}: {response.text}")

        # Only log to stdout for human-readability (not structured JSON)
        if isinstance(event, dict):
            stdout_logger.info(json.dumps(event))
        else:
            stdout_logger.info(event)

    except Exception as e:
        # Avoid logging this error via Splunk again!
        print(f"[Splunk Logging Error] {e}")


