import json
import os
import requests
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

APP_NAME = os.environ.get('APP_NAME', 'youkaichatbot-ds')
KEY = os.environ.get('KEY', 'a37c41e9-c6d8-4c2d-afc9-82255c13371b')
PROCESS = os.environ.get('PROCESS', 'worker')

HEADERS = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": "Bearer " + KEY,
    "Content-Type": "application/json"
}


def scale(size):
    payload = {'quantity': size, 'type': 'worker'}
    json_payload = json.dumps(payload)
    url = "https://api.heroku.com/apps/" + APP_NAME + "/formation/" + PROCESS
    try:
        result = requests.patch(url, headers=HEADERS, data=json_payload)
    except Exception as error:
        print("test!")
        return str(error)
    if result.status_code == 200:
        return "Success!"
    else:
        return "Failure"


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    def job():
        print('Scaling ...')
        print(scale(0))


sched.start()
