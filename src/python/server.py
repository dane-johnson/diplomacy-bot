import os
import sys
import pickle
import re
import requests
from dotenv import load_dotenv
load_dotenv()

from util import group_by
from gameboard import gameboard, starting_positions
from image import draw_gameboard
from interfaces import SlackInterface, CLIInterface, DiscordInterface

FACTIONS = frozenset(["austria-hungary", "england", "france", "germany", "italy", "russia", "turkey"])
MODES = frozenset(["pregame", "ingame"])

gamestate = {
  "players": {},
  "units": {},
  "orders": {},
  "mode": "pregame",
  "gameboard": gameboard,
  "dislodged_units": {},
  "invalid_retreats": set([])
}

filename = None

#################### INPUT ####################

def handle_event(event):
  if event["type"] == 'app_mention':
    handle_in_channel_message(event)
  elif event["type"] == 'message':
    order = parse_order(event['text'])
    if order:
      if gamestate['mode'] == get_order_mode(order):
        error = order_error(order, event['user'])
        if not error:
          send_message_im("Order Recieved!", event["channel"])
          if gamestate['mode'] == 'active':
            add_order(order)
          else:
            add_retreat_order(order)
          if filename:
            save_gamestate()
        else:
          send_message_im(error, event["channel"])
      else:
        send_message_im("You can't send that order now!", event['channel'])
    else:
      send_message_im("I don't know what you mean!", event["channel"])

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

  display_regex = r"display (.*)"
  display_groups = re.search(display_regex, event['text'].lower())
  if display_groups:
    item = display_groups.group(1)
    if item == 'factions':
      faction_string = print_factions()
      send_message_channel(faction_string)
    elif item == 'board':
      gameboard_img = draw_gameboard(gamestate['gameboard'])
      send_image_channel(gameboard_img)
    else:
      send_message_channel("I don't know what %s is." % item)

  amend_regex = r"amend (.*)"
  amend_groups = re.search(amend_regex, event['text'].lower())
  if amend_groups:
    amendments_regex = r"([-a-z]+) (army|fleet|remove) at ([a-z]{3})"
    matches = re.findall(amendments_regex, amend_groups.group(1))
    for match in matches:
      faction, piece, territory = match
      if faction in FACTIONS and territory in gamestate['gameboard']:
        if piece == 'remove':
          remove_piece(territory)
        else:
          add_piece('%s %s' % (faction, piece), territory)

  start_regex = r"start"
  start_groups = re.search(start_regex, event['text'].lower())
  if start_groups:
    start_game()

  end_regex = r"end$"
  end_groups = re.search(end_regex, event['text'].lower())
  if end_groups:
    if gamestate['mode'] == 'active':
      end_active_mode()
    else:
      end_retreat_mode()

  if filename:
    save_gamestate()

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
    if support_groups.group(3):
      order['to'] = support_groups.group(3)
    return order

  convoy_regex = r"fleet\s([a-z]{3})\sconvoys\sarmy\s([a-z]{3})\sto\s([a-z]{3})"
  convoy_groups = re.match(convoy_regex, order)
  if convoy_groups:
    return {'action': 'convoy', 'territory': convoy_groups.group(1), 'from': convoy_groups.group(2), 'to': convoy_groups.group(3)}

  disband_regex = r"(?:army|fleet)\s([a-z]{3})\sdisbands"
  disband_groups = re.match(disband_regex, order)
  if disband_groups:
    return {'action': 'disband', 'territory': disband_groups.group(1)}

  retreat_regex = r"(?:fleet|army)\s([a-z]{3})\sretreats\sto\s([a-z]{3})"
  retreat_groups = re.match(retreat_regex, order)
  if retreat_groups:
    return {'action': 'retreat', 'territory': retreat_groups.group(1), 'to': retreat_groups(2)}

def order_error(order, user):
  board = gamestate['gameboard']
  territories_in_order = map(lambda x: order.get(x, None), ['territory', 'to', 'from', 'supporting'])
  for territory in territories_in_order:
    ## Make sure territory/to/from/supports is on the board
    if territory and territory not in gamestate['gameboard']:
      return "Territory %s is not valid" % territory
  ## Make sure the user can control this army/navy
  if gamestate['gameboard'][order['territory']]['piece'].split()[0] != get_faction(user):
    return "%s does not control %s" % (get_faction(user), order['territory'])
  piece = get_piece(order['territory'])
  if order['action'] == 'convoy':
    if piece.split()[1] == 'army':
      return "You may not order an army to convoy"
    if board[order['territory']]['type'] != 'water':
      return "You cannot convoy from a coastal territory"
    if get_piece(order['from']) == 'none' or get_piece(order['from']).split()[1] == 'fleet':
      return "You can only convoy an army"
    if board[order['to']]['type'] != 'coastal' or board[order['from']]['type'] != 'coastal':
      return "You may only convoy between coastal territories"
  if order['action'] == 'move/attack':
   ## Don't allow armies to move to water spaces
   if board[order['to']]['type'] == 'water' and piece.split()[1] == 'army':
     return "Cannot move army to water space"
   ## Don't allow fleets to move to land spaces
   if board[order['to']]['type'] == 'land' and piece.split()[1] == 'fleet':
     return "Cannot move fleet to land space"
   if piece.split()[1] == 'fleet' and board[order['to']] not in board[order['territory']]['borders']:
     return "Fleets can only move to adjacent spaces"
   ## Don't allow movement to/from land or water spaces from/to non-adjacent spaces
   if board[order['territory']]['type'] == 'land' and order['to'] not in board[order['territory']]['borders'] or \
      board[order['to']]['type'] == 'land' and order['territory'] not in board[order['to']]['borders']:
     return "Moving to this non-adjacent space is illegal"
  if order['action'] == 'support':
    if order['to'] not in board[order['territory']]['borders']:
      return "Cannot support %s from a non-adjacent space" % order['to']
    if board[order['to']]['type'] == 'land' and piece.split()[1] == 'fleet':
      return "A fleet cannot support a land territory"
    if board[order['to']]['type'] == 'water' and piece.split()[1] == 'army':
      return "An army cannot support a water territory"
  return None

def get_order_mode(order):
  if order['action'] in frozenset(['retreat', 'disband']):
    return 'retreat'
  if order['action'] in frozenset(['move/attack', 'hold', 'convoy', 'support']):
    return 'active'


#################### PRINT ####################

def print_factions():
  string = ""
  for faction in FACTIONS:
    string += "%s: " % faction
    for player in gamestate['players'][faction]:
      string += "<@%s>, " % player
    string += "\n"
  return string

def print_retreats():
  displacement_map = {faction: [] for faction in FACTIONS}
  for territory in gamestate['dislodged_units']:
    (piece, attacking_territory) = gamestate['dislodged_units'][territory]
    [faction, unit] = piece
    displacement_map[faction].append((territory, unit, attacking_territory))
  for faction in displacement_map:
    print "%s:" % faction
    for territory, unit, attacking_territory in displacement_map(faction):
      print "%s displaced from %s by unit at %s" % (unit, territory, attacking_territory)


#################### GETTERS/SETTERS/MUTATORS ####################

def add_order(order):
  ## Find and remove any existing orders for this unit
  if order['territory'] in gamestate['orders']:
    del gamestate['orders'][order['territory']]
  gamestate['orders'][order['territory']] = order

def get_order(space):
  if space in gamestate['orders']: return gamestate['orders'][space]
  else: return None

def add_retreat_order(order):
  if order['territory'] in gamestate['retreat_orders']:
    del gamestate['retreat_order'][order['territory']]
  gamestate['orders'][order['territory']] = order

def create_retreat_orders():
  for territory in gamestate['dislodged_units']:
    add_retreat_order({'action': 'disband', 'territory': territory})

def add_piece(piece, territory):
  gamestate['gameboard'][territory]['piece'] = piece

def remove_piece(territory):
  gamestate['gameboard'][territory]['piece'] = 'none'

def get_piece(territory):
  return gamestate['gameboard'][territory]['piece']

def get_territory(territory):
  return gamestate['gameboard'][territory]

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

def dislodge_territory(territory, attacker_origin):
  gamestate['dislodged_units'][territory] = (get_piece(territory), attacker_origin)
  del gamestate['gameboard'][territory]
  del gamestate['orders'][territory]

def is_illegal_move(order):
  board = gamestate['gameboard']
  orders = gamestate['orders']
  relevant_convoys = set(filter(lambda x: orders[x]['action'] == 'convoy' and orders[x]['from'] == order['territory'] and orders[x]['to'] == order['to'], gamestate['orders']))
  ## Perform a BFS to see if we can reach 'to' from 'territory'
  queue = [order['territory']]
  while len(queue) > 0:
    territory = queue[0]
    del queue[0]
    if territory in board[order['to']]['borders']:
      return False
    for space in board[territory]['borders']:
      if space in relevant_convoys:
        queue.append(space)
        relevant_convoys.remove(space)
  return True

def is_convoyed(order):
  orders = gamestate['orders']
  bordering_spaces = get_territory(order['territory'])['borders']
  if order['to'] not in bordering_spaces:
    return True
  relevant_convoys = set(filter(lambda x: orders[x]['action'] == 'convoy' and orders[x]['from'] == order['territory'] and orders[x]['to'] == order['to'], gamestate['orders']))
  if len(filter(lambda x: x in bordering_spaces, relevant_convoys)) == 0:
    return False
  return True
def increase_support(territory):
  order = get_order(territory)
  if order['action'] not in frozenset(['move/attack', 'hold']):
    return
  if 'support' not in order:
    order['support'] = 1
  else:
    order['support'] += 1

def determine_losers(orders):
  max_support = max(orders, key=lambda x: x['support'])['support']
  losers = filter(lambda x: x['support'] < max_support, orders)
  if len(losers) < len(orders) - 1:
    gamestate["invalid_retreats"].add(orders[1]['to'])
    return orders
  return losers


#################### CONTROL ####################

def end_active_mode():
  resolve_orders()
  update_territories()
  create_retreat_orders()
  gamestate['mode'] = 'retreat'
  send_message_channel('Retreat!')

def end_retreat_mode():
  resolve_retreat_orders()
  gamestate['mode'] = 'active'
  new_round()
  send_message_channel('Place your orders!')

def start_game():
  global gamestate
  if gamestate['mode'] != 'pregame':
    send_message_channel("Game is already on!")
  else:
    empty_factions = filter(lambda x: len(gamestate['players'][x]) == 0, FACTIONS)
    if len(empty_factions) > 0:
      send_message_channel("These factions have no members: %s" % ", ".join(empty_factions))
    else:
      gamestate['mode'] = 'active'
      new_round()
      send_message_channel("@here Game on!!!")

def new_round():
  if 'season' not in gamestate or gamestate['season'] == 'fall':
    gamestate['season'] = 'spring'
  else:
    gamestate['season'] = 'fall'
  ## Every piece holds by default
  gamestate['orders'] = {}
  for territory in filter(lambda x: gamestate['gameboard'][x]['piece'] != 'none', gamestate['gameboard']):
    add_order({'action': 'hold', 'territory': territory})
  gamestate['retreat_orders'] = {}
  gamestate['dislodged_units'] = {}
  gamestate['invalid_retreats'] = set([])

def resolve_orders():
  board = gamestate['gameboard']
  orders = gamestate['orders']

  ## Break all support and convoy orders
  for territory in orders:
    order = orders[territory]
    if order['action'] == 'move/attack' and order['to'] in orders:
      if orders[order['to']]['action'] == 'support' and orders[order['to']]['to'] != territory:
        add_order({'territory': order['to'], 'action': 'hold'})
      if orders[order['to']]['action'] == 'convoy':
        add_order({'territory': order['to'], 'action': 'hold'})

  ## Determine which units are successfully moved, and which are convoyed
  for territory in orders:
    order = orders[territory]
    if order['action'] == 'move/attack':
      if is_illegal_move(order):
        add_order({'territory': territory, 'action': 'hold', 'is_convoyed': False})
      else:
        order['is_convoyed'] = is_convoyed(order)

  ## Calculate support for each attacking and holding piece
  for territory in orders:
    order = get_order(territory)
    if order['action'] in frozenset(['move/attack', 'hold']):
      increase_support(territory)
    elif order['action'] == 'support':
      increase_support(order['supporting'])

  ## Find and resolve swap standoffs
  for territory in orders.copy():
    order = get_order(territory)
    if order['action'] == 'move/attack':
      attacked_territory = order['to']
      attacked_territory_order = get_order(attacked_territory)
      if attacked_territory_order and \
      attacked_territory < territory and \
      attacked_territory_order['action'] == 'move/attack' and \
      attacked_territory_order['to'] == territory and \
      not order['is_convoyed'] and \
      not attacked_territory_order['is_convoyed']:
        ## Swap standoff
        if order['support'] > attacked_territory_order['support']:
          dislodge_territory(attacked_territory, territory)
        elif order['support'] < attacked_territory_order['support']:
          dislodge_territory(territory, attacked_territory)
        else:
          add_order({'territory': territory, 'action': 'hold', 'support': 1})
          add_order({'territory': attacked_territory, 'action': 'hold', 'support': 1})
  ## Find and resolve move/move standoffs
  attacking_orders = filter(lambda x: x['action'] == 'move/attack', orders.values())
  for group in filter(lambda x: len(x) > 1, group_by(attacking_orders, 'to')):
    losers = determine_losers(group)
    for order in losers:
      add_order({'territory': order['territory'], 'action': 'hold', 'support': 1})
    if len(losers) == len(group):
      gamestate['invalid_retreats'].add(group[0]['to'])
  ## Loop and resolve move/hold standoffs
  standoff_found = True
  while standoff_found:
    standoff_found = False
    for territory in orders.copy():
      order = get_order(territory)
      if order['action'] == 'move/attack':
        attacked_territory = order['to']
        attacked_territory_order = get_order(attacked_territory)
        if attacked_territory_order and attacked_territory_order['action'] == 'hold':
          standoff_found = True
          if order['support'] > attacked_territory_order['support'] and get_piece(attacked_territory).split()[0] != get_piece(territory).split()[0]:
            dislodge_territory(attacked_territory, territory)
            break ## Can't keep iterating over orders because it has been modified TODO find a better way to do this
          else:
            add_order({'territory': territory, 'action': 'hold', 'support': 1})

def resolve_retreat_orders():
  retreats = filter(lambda x: x['action'] == 'retreat', gamestate['retreat_orders'].values())
  groups = group_by(retreats, 'to')
  for group in filter(lambda x: len(x) == 1, groups):
    [valid_retreat] = group
    territory = valid_retreat['territory']
    piece = gamestate['dislodged_units'][territory][0]
    add_piece(piece, territory)

def update_territories():
  attacking_orders = filter(lambda x: x['action'] == 'move/attack', gamestate['orders'].values())
  new_placements = []
  ## Remove moving pieces, record where they are going
  for order in attacking_orders:
    new_placements.append((order['to'], get_piece(order['territory'])))
    remove_piece(order['territory'])
  ## Add back moved pieces
  for territory, piece in new_placements:
    add_piece(piece, territory)


#################### PERSISTENCE ####################

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
  for space in gamestate['gameboard']:
    if 'supply' in gamestate['gameboard'][space] and gamestate['gameboard'][space]['supply'] != 'none':
      if gamestate['gameboard'][space]['supply'] == 'neutral':
        gamestate['gameboard'][space]['controller'] = 'none'
      else:
        gamestate['gameboard'][space]['controller'] = gamestate['gameboard'][space]['supply']
    gamestate['gameboard'][space]['piece'] = 'none'
    gamestate['gameboard'][space]['borders'] = frozenset(gamestate['gameboard'][space]['borders'])
  for pos in starting_positions:
    gamestate['gameboard'][pos]['piece'] = starting_positions[pos]


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
  if os.environ['CHAT_APPLICATION'] == 'slack':
    interface = SlackInterface(handle_event)
  elif os.environ['CHAT_APPLICATION'] == 'discord':
    interface = DiscordInterface(handle_event)
  else:
    interface = CLIInterface(handle_event)
  send_message_im = interface.send_message_im
  send_message_channel = interface.send_message_channel
  send_image_channel = interface.send_image_channel
  interface.run()
