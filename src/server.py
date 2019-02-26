import os
import sys
import pickle
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
  "mode": "active"
}

filename = None

@app.route("/event", methods=['POST'])
def return_request_challenge():
  params = request.get_json()
  print params
  if 'challenge' in params:
    return request.get_json()['challenge']
  event = params["event"]
  if event["type"] == 'app_mention':
    handle_in_channel_message(event)
  elif event["type"] == 'message' and \
       not ("subtype" in event and event["subtype"] == "bot_message"):
    order = parse_order(event['text'])
    if order:
      if gamestate['mode'] == 'active':
        send_message_im("Order Recieved!", event["channel"])
        print order 
      else:
        send_message_im("Wait to send orders until the game is started!", event['channel'])
    else:
      send_message_im("I don't know what you mean!", event["channel"])
  return "OK"

def send_message_channel(message):
  ## Sick of having to check slack, allow an environment variable to print to screen
  if os.environ["DIPLOMACY_DEMO"]:
    print 'CHANNEL-MESSAGE:%s' % message
    return
  
  headers = {
    "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
  }
  body = {
    "text": message,
    "channel": "#diplomacy"
  }

  requests.post(SLACK_URL, data=body, headers=headers)

def send_message_im(message, app_channel):
    ## Sick of having to check slack, allow an environment variable to print to screen
  if os.environ["DIPLOMACY_DEMO"]:
    print 'IM-%s:%s' % (app_channel, message)
    return

  headers = {
    "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
  }
  body = {
    "text": message,
    "channel": app_channel,
  }

  requests.post(SLACK_URL, data=body, headers=headers)

def parse_order(order):
  formatted_order = order.strip().lower()
  
  hold_regex = r"(?:army|fleet)\s([a-z]{3})\sholds"
  hold_groups = re.match(hold_regex, order)
  if hold_groups:
    return {'action': 'hold', 'territory': hold_groups.group(1)}

  move_attack_regex = r"(?:army|fleet)\s([a-z]{3})\sto\s([a-z]{3})"
  move_attack_groups = re.match(move_attack_regex, order)
  if move_attack_groups:
    return {'action': 'move/attack', 'territory': move_attack_groups.group(1), 'to': move_attack_groups.group(2)}

  support_regex = r"(?:army|fleet)\s([a-z]{3})\ssupports\s(?:army|fleet)\s([a-z]{3})(?:\sto\s)?([a-z]{3})?"
  support_groups = re.match(support_regex, order)
  if support_groups:
    order = {'action': 'support', 'territory': support_groups.group(1), 'supporting': support_groups.group(2)}
    print support_groups.group(3)
    if support_groups.groups(3):
      order['to'] = support_groups.group(3)
    return order

  convoy_regex = r"(?:fleet)\s([a-z]{3})\sconvoys\s(?:army)\s([a-z]{3})\sto\s([a-z]{3})"
  convoy_groups = re.match(convoy_regex, order)
  if convoy_groups:
    return {'action': 'convoy', 'territory': convoy_groups.group(1), 'from': convoy_groups.group(2), 'to': convoy_groups.group(3)}

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
      add_to_faction(faction, user)
      send_message_channel("<@%s> you are registered to faction %s" % (user, faction))

  display_regex = r"display (factions)"
  display_groups = re.search(display_regex, event['text'].lower())
  if display_groups:
    item = display_groups.group(1)
    if item == 'factions':
      faction_string = print_factions()
      send_message_channel(faction_string)

  start_regex = r"start"
  start_groups = re.search(start_regex, event['text'].lower())
  if start_groups:
    start_game()

  if filename:
    save_gamestate()

def print_factions():
  string = ""
  for faction in FACTIONS:
    string += "%s: " % faction
    for player in gamestate['players'][faction]:
      string += "<@%s>, " % player
    string += "\n"
  return string

def get_all_players():
  return reduce(lambda x, y: x | y, gamestate['players'].values())

def get_faction(player):
  for faction in FACTIONS:
    if player in gamestate['players'][faction]:
      return faction

def add_to_faction(faction, player):
  global gamestate
  if player in get_all_players():
    ## the player wants to switch teams
    current_faction = get_faction(player)
    gamestate['players'][current_faction].remove(player)
  gamestate['players'][faction].add(player)

def start_game():
  global gamestate
  if gamestate['mode'] != 'pregame':
    send_message_channel("Game is already on!")
  else:
    empty_factions = filter(lambda x: len(gamestate['players'][x]) == 0, FACTIONS)
    if len(empty_factions) > 0:
      send_message_channel("These factions have no members: %s" % ", ".join(empty_factions))
    else:
      gamestate['mode'] == 'active'
      send_message_channel("@here game on!!!")

def restore_gamestate():
  global gamestate
  file = open(filename, 'r')
  gamestate = pickle.load(file)
  file.close()

def save_gamestate():
  file = open(filename, 'w')
  pickle.dump(gamestate, file)
  file.close()

def init_gamestate():
  ## Add all factions with empty team names
  global gamestate
  for faction in FACTIONS:
    gamestate["players"][faction] = set([])

if __name__ == '__main__':
  if len(sys.argv) == 2:
    filename = sys.argv[1]
    if os.path.isfile(filename):
      restore_gamestate()
    else:
      init_gamestate()
      save_gamestate()
  else:
    init_gamestate()
  app.run('0.0.0.0')
