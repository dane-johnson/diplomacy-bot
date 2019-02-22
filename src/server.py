import os
import requests
from dotenv import load_dotenv
load_dotenv()
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
  if params["type"] == 'app_mention':
    send_message_channel("hi everyone")
  elif params["type"] == 'message':
    send_message_im("hi you", params['user'])
  return "OK"

def send_message_channel(message):
  headers = {
    "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
  }
  body = {
    "text": message,
    "channel": "#diplomacy"
  }

  requests.post(SLACK_URL, data=body, headers=headers)

def send_message_im(message, user):
  headers = {
    "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
  }
  body = {
    "text": message,
    "channel": user,
  }

  requests.post(SLACK_URL, data=body, headers=headers)

if __name__ == '__main__':
  app.run('0.0.0.0', port=80)
