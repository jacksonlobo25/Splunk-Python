# Common/splunk_logger.py
import requests
import json
import time
import logging

# Splunk Config
SPLUNK_HEC_URL = 'http://34.41.226.221:8088/services/collector'
SPLUNK_TOKEN = '16e22809-f1a7-4972-b91d-b724a7cfb02b'

# Setup stdout logger
stdout_logger = logging.getLogger("stdout_logger")
stdout_logger.propagate = False

if not stdout_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    stdout_logger.addHandler(handler)
    stdout_logger.setLevel(logging.INFO)

def log_to_splunk(
    message,
    status_code=None,
    ip_address=None,
    response_time=None,
    method=None,
    endpoint=None,
    user_agent=None,
    extra_data=None,
    sourcetype='web-app',
    index='main',
    host='flask-app'
):
    """
    Send structured logs to Splunk.
    """
    headers = {
        'Authorization': f'Splunk {SPLUNK_TOKEN}',
        'Content-Type': 'application/json'
    }

    event_data = {
        'message': message,
        'status_code': status_code,
        'ip_address': ip_address,
        'response_time_ms': response_time,
        'method': method,
        'endpoint': endpoint,
        'user_agent': user_agent,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    }

    if extra_data and isinstance(extra_data, dict):
        event_data.update(extra_data)

    payload = {
        'event': event_data,
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

        stdout_logger.info(json.dumps(event_data))

    except Exception as e:
        print(f"[Splunk Logging Error] {e}")
