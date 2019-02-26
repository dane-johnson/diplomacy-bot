import os
import re
import requests
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request
app = Flask(__name__)

SLACK_URL = "https://slack.com/api/chat.postMessage"

FACTIONS = frozenset(["austria-hungary", "england", "france", "germany", "italy", "russia", "turkey"])
MODES = frozenset(["pregame", "ingame"])

gamestate = {
  "players": {},
  "units": {},
  "orders": [],
  "mode": "pregame"
}

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
    handle_in_channel_message(event)
  elif event["type"] == 'message' and \
       not ("subtype" in event and event["subtype"] == "bot_message"):
    if validate_order(event['text']):
      send_message_im("Order Recieved!", event["channel"])
    else:
      send_message_im("I don't know what you mean!", event["channel"])
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

def validate_order(order):
  formatted_order = order.strip().lower()
  order_regex = r"(army|fleet)\s[a-z]{3}\sholds"
  return re.search(order_regex, formatted_order) != None

def handle_in_channel_message(event):
  register_regex = r"register ([-a-z]+)"
  register_groups = re.search(register_regex, event['text'].lower())
  if register_groups:
    if gamestate['mode'] != 'pregame': ## Sanity check
      send_message_channel("Cannot register while the game is on!")
      return
    faction = register_groups.group(1)
    if not faction in FACTIONS:
      send_message_channel("%s is not a valid faction" % faction)
    else:
      user = event['user']
      send_message_channel("<@%s> you are registered to faction %s" % (user, faction))

if __name__ == '__main__':
  app.run('0.0.0.0')
