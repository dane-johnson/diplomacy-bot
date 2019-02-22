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
  event = params["event"]
  if event["type"] == 'app_mention':
    send_message_channel("hi everyone")
  elif event["type"] == 'message' and \
       not ("subtype" in event and event["subtype"] == "bot_message"):
    send_message_im("hi you", event['channel'])
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

def send_message_im(message, app_channel):
  headers = {
    "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
  }
  body = {
    "text": message,
    "channel": app_channel,
  }

  requests.post(SLACK_URL, data=body, headers=headers)

if __name__ == '__main__':
  app.run('0.0.0.0')
