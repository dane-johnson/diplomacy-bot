import os
import requests
from flask import Flask, request
app = Flask(__name__)

SLACK_URL = "https://slack.com/api/chat.postMessage"

@app.route("/")
def hello():
  return "Hello World"

@app.route("/event", methods=['POST'])
def returnRequestChallenge():
  params = request.get_json()
  print params
  if 'challenge' in params:
    return request.get_json()['challenge']
  return "OK"

def send_message(message):
  headers = {
    "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
  }
  body = {
    "text": "Hi there",
    "channel": "#diplomacy",
  }

  requests.post(SLACK_URL, data=body, headers=header)

if __name__ == '__main__':
  app.run('0.0.0.0', port=80)
