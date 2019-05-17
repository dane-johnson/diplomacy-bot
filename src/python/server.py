# Diplomacy bot is a bot to play diplomacy on Slack and Discord
# Copyright (C) 2019 Dane Johnson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License 
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import pickle
import re
import requests
from string import capitalize
from dotenv import load_dotenv
load_dotenv()

from util import group_by
from gameboard import gameboard, starting_positions
from image import draw_gameboard
from interfaces import SlackInterface, CLIInterface, DiscordInterface

FACTIONS = frozenset(["austria-hungary", "england", "france", "germany", "italy", "russia", "turkey"])
MODES = frozenset(["pregame", "active", 'retreat', 'adjustments'])

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
    text = event['text']
    if is_display_request(text):
      private_display(text, event['user'], event['channel'])
    else:
      order = parse_order(event['text'], event['user'])
      if order:
        if gamestate['mode'] == get_order_mode(order):
          error = order_error(order, event['user'])
          if not error:
            send_message_im("Order Recieved!", event["channel"])
            if gamestate['mode'] == 'active':
              add_order(order)
            elif gamestate['mode'] == 'retreat':
              add_retreat_order(order)
            elif gamestate['mode'] == 'adjustments':
              add_adjustments_order(order)
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
      show_board()
    elif item == 'retreats':
      retreats_string = print_retreats()
      send_message_channel(retreats_string)
    elif item == 'orders':
      user = event['user']
      inform_orders(user, user) ## TODO this only works on Slack
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
          if gamestate['mode'] == 'active':
            add_order({'territory': territory, 'action': 'hold'})

  start_regex = r"start"
  start_groups = re.search(start_regex, event['text'].lower())
  if start_groups:
    start_game()

  end_regex = r"end$"
  end_groups = re.search(end_regex, event['text'].lower())
  if end_groups:
    if gamestate['mode'] == 'active':
      end_active_mode()
    elif gamestate['mode'] == 'retreat':
      end_retreat_mode()
    elif gamestate['mode'] == 'adjustments':
      end_adjustments_mode()

  if filename:
    save_gamestate()

def private_display(text, user, im_channel):
  display_regex = r"display (.*)"
  display_groups = re.match(display_regex, text)
  if display_groups:
    item = display_groups.group(1)
    if item == 'factions':
      faction_string = print_factions()
      send_message_im(faction_string, im_channel)
    elif item == 'retreats':
      retreats_string = print_retreats
      send_message_im(retreats_string, im_channel)
    elif item == 'orders':
      inform_orders(user, im_channel)
    elif item == 'board':
      send_message_im("I can't send images to DM channels yet, ask me in the group channel", im_channel)
    else:
      send_message_im("I don't know what %s is." % item, im_channel)

def parse_order(order, user):
  faction = get_faction(user)
  formatted_order = order.strip().lower()
  
  hold_regex = r"(?:army|fleet)\s([a-z]{3})\sholds"
  hold_groups = re.match(hold_regex, formatted_order)
  if hold_groups:
    return {'action': 'hold', 'territory': hold_groups.group(1)}

  move_attack_regex = r"(?:army|fleet)\s([a-z]{3})\sto\s([a-z]{3})"
  move_attack_groups = re.match(move_attack_regex, formatted_order)
  if move_attack_groups:
    return {'action': 'move/attack', 'territory': move_attack_groups.group(1), 'to': move_attack_groups.group(2)}

  support_regex = r"(?:army|fleet)\s([a-z]{3})\ssupports\s(?:army|fleet)\s([a-z]{3})(?:\sto\s)?([a-z]{3})?"
  support_groups = re.match(support_regex, formatted_order)
  if support_groups:
    order = {'action': 'support', 'territory': support_groups.group(1), 'supporting': support_groups.group(2)}
    if support_groups.group(3):
      order['to'] = support_groups.group(3)
    return order

  convoy_regex = r"fleet\s([a-z]{3})\sconvoys\sarmy\s([a-z]{3})\sto\s([a-z]{3})"
  convoy_groups = re.match(convoy_regex, formatted_order)
  if convoy_groups:
    return {'action': 'convoy', 'territory': convoy_groups.group(1), 'from': convoy_groups.group(2), 'to': convoy_groups.group(3)}

  disband_regex = r"(?:army|fleet)\s([a-z]{3})\sdisbands"
  disband_groups = re.match(disband_regex, formatted_order)
  if disband_groups:
    return {'action': 'disband', 'territory': disband_groups.group(1)}

  retreat_regex = r"(?:fleet|army)\s([a-z]{3})\sretreats\sto\s([a-z]{3})"
  retreat_groups = re.match(retreat_regex, formatted_order)
  if retreat_groups:
    return {'action': 'retreat', 'territory': retreat_groups.group(1), 'to': retreat_groups.group(2)}

  add_regex = r"add\s(?:fleet|army)\sat\s[a-z]{3}"
  if re.match(add_regex, formatted_order):
    group_regex = r"(fleet|army)\s(?:at\s)([a-z]{3})"
    matches = re.findall(group_regex, formatted_order)
    groups = []
    for match in matches:
      unit, territory = match
      groups.append((unit, territory))
    return {'action': 'add', 'groups': groups, 'faction': faction}
  
  remove_regex = r"remove\s(?:fleet|army)\sat\s[a-z]{3}"
  if re.match(remove_regex, formatted_order):
    group_regex = r"(fleet|army)\s(?:at\s)([a-z]{3})"
    matches = re.findall(group_regex, formatted_order)
    groups = []
    for match in matches:
      unit, territory = match
      groups.append((unit, territory))
    return {'action': 'remove', 'groups': groups, 'faction': faction}
  

def order_error(order, user):
  board = gamestate['gameboard']
  if gamestate['mode'] == 'adjustments':
    territories_in_order = map(lambda x: x[1], order['groups'])
  else:
    territories_in_order = map(lambda x: order.get(x, None), ['territory', 'to', 'from', 'supporting'])
  dislodged_units = gamestate['dislodged_units']
  for territory in territories_in_order:
    ## Make sure territory/to/from/supports is on the board
    if territory and territory not in gamestate['gameboard']:
      return "Territory %s is not valid" % territory
  ## Make sure the user can control this army/navy
  if gamestate['mode'] == 'active':
    if gamestate['gameboard'][order['territory']]['piece'].split()[0] != get_faction(user):
      return "%s does not control %s" % (get_faction(user), order['territory'])
    piece = get_piece(order['territory'])
  if gamestate['mode'] == 'retreat':
    if gamestate['dislodged_units'][order['territory']][0].split()[0] != get_faction(user):
      return "%s does not control the unit dislodged from %s" % (get_faction(user), order['territory'])
    piece = dislodged_units[order['territory']][0]
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
   if piece.split()[1] == 'fleet':
     if order['to'] not in board[order['territory']]['borders']:
       return "Fleets can only move to adjacent spaces"
     if board[order['territory']]['type'] == 'coastal' and board[order['to']]['type'] == 'coastal' and order['to'] not in board[order['territory']]['coastal_borders']:
       return "Fleets can only move along coastlines"
   ## Don't allow movement to/from land or water spaces from/to non-adjacent spaces
   if board[order['territory']]['type'] == 'land' and order['to'] not in board[order['territory']]['borders'] or \
      board[order['to']]['type'] == 'land' and order['territory'] not in board[order['to']]['borders']:
     return "Moving to this non-adjacent space is illegal"
  if order['action'] == 'support':
    if 'to' in order:
      supported_territory = order['to']
    else:
      supported_territory = order['supporting']
    if supported_territory not in board[order['territory']]['borders']:
      return "Cannot support %s from a non-adjacent space" % order['to']
    if board[supported_territory]['type'] == 'land' and piece.split()[1] == 'fleet':
      return "A fleet cannot support a land territory"
    if board[supported_territory]['type'] == 'water' and piece.split()[1] == 'army':
      return "An army cannot support a water territory"
    if board[supported_territory]['type'] == 'coastal' and board[territory]['type'] == 'coastal' and piece.split()[1] == 'fleet' and supported_territory not in board[territory]['coastal_borders']:
      return "Fleets can only support along the coastlines"
  if order['action'] == 'retreat':
    # Don't allow retreating to occupied spaces
    if board[order['to']]['piece'] != 'none':
      return "You cannot retreat to %s because there is already a unit there" % order['to']
    # Don't allow retreating to non-adjacent spaces
    if order['to'] not in board[order['territory']]['borders']:
      return "You cannot retreat to a spaces that is not adjacent to %s" % order['territory']
    # Don't allow armies to retreat to water spaces
    if board[order['to']]['type'] == 'water' and piece.split()[1] == 'army':
      return "An army cannot retreat to a water space"
    # Don't allow fleets to retreat to land spaces
    if board[order['to']]['type'] == 'army' and piece.split()[1] == 'fleet':
      return "A fleet cannot retreat to a land space"
    # Don't allow retreating to the space where the attack came from
    if order['to'] == dislodged_units[order['territory']][1]:
      return "You cannot retreat to %s because you were attacked from there" % order['territory']
    # Don't allow retreating to spaces left open by standoffs
    if order['to'] in gamestate['invalid_retreats']:
      return "You cannot retreat to %s because it was left vacant by a standoff" % order['territory']
  if order['action'] == 'add':
    faction = order['faction']
    for unit, territory in order['groups']:
      # Don't allow adding to non-supply territories
      if 'supply' not in gameboard[territory] or gameboard[territory]['supply'] == 'none':
        return "%s is not a supply center" % territory
      # Don't allow adding at occupied spaces
      if get_piece(territory) != 'none':
        return "You cannot add at %s because it is already occupied" % territory
      # Don't allow adding at spaces that you do not control
      if territory not in get_home_territories(faction) or gameboard[territory]['supply'] != faction:
        return "%s is not one of your controlled home territories" % territory
      # Don't allow adding fleets to land spaces
      if unit == 'fleet' and gameboard[territory]['type'] == 'land':
        return "Cannot add a fleet to a non-coastal city"
    # Don't allow more adds than the delta
    if len(order['groups']) > get_unit_delta(order['faction']):
      return "You can only add up to %d units" % get_unit_delta(order['faction'])
  if order['action'] == 'remove':
    faction = order['faction']
    for unit, territory in order['groups']:
      # Don't allow removal of an empty space
      if gameboard[territory]['piece'] == 'none':
        return "You cannot remove %s as it is empty" % territory
      # Don't allow removal from another faction
      if gameboard[territory]['piece'].split()[0] != faction:
        return "You cannot remove %s as it is controlled by another faction" % territory
    # Don't allow any more or less removals than the delta
    if len(order['groups']) != -get_unit_delta(order['faction']):
      return "You must remove exactly %d units" % -get_unit_delta(order['faction'])
  return None

def get_order_mode(order):
  if order['action'] in frozenset(['retreat', 'disband']):
    return 'retreat'
  if order['action'] in frozenset(['move/attack', 'hold', 'convoy', 'support']):
    return 'active'
  if order['action'] in frozenset(['add', 'remove']):
    return 'adjustments'


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
  string = ""
  displacement_map = {faction: [] for faction in FACTIONS}
  for territory in gamestate['dislodged_units']:
    (piece, attacking_territory) = gamestate['dislodged_units'][territory]
    [faction, unit] = piece.split()
    displacement_map[faction].append((territory, unit, attacking_territory))
  for faction in displacement_map:
    if len(displacement_map[faction]) > 0:
      string += '%s: \n' % faction
      for territory, unit, attacking_territory in displacement_map[faction]:
        string += "\t%s dislodged from %s by unit at %s\n" % (unit, territory, attacking_territory)
  return string

def show_board():
  gameboard_img = draw_gameboard(gamestate['gameboard'])
  send_image_channel(gameboard_img)

def inform_adjustments():
  for faction in FACTIONS:
    for user in gamestate['players'][faction]:
      delta = get_unit_delta(faction)
      if delta > 0:
        send_message_channel("<@%s> you may add %d units" % (user, delta))
      elif delta < 0:
        send_message_channel("<@%s> you must remove %s units" % (user, -delta))

def inform_orders(user, channel):
  faction = get_faction(user)
  for territory in gamestate['gameboard']:
    if get_piece(territory).split()[0] == faction:
      send_message_im(str(get_order(territory)), channel)

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
    del gamestate['retreat_orders'][order['territory']]
  gamestate['retreat_orders'][order['territory']] = order
def add_adjustments_order(order):
  if order['faction'] in gamestate['adjustments_orders']:
    del gamestate['adjustments_orders'][order['faction']]
  gamestate['adjustments_orders'][order['faction']] = order
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
  gamestate['gameboard'][territory]['piece'] = 'none'
  del gamestate['orders'][territory]

def is_display_request(text):
  display_regex = r"display"
  return re.match(display_regex, text)

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

def count_supply_centers(faction):
  return len(filter(lambda x: 'supply' in x and x['supply'] == faction, gamestate['gameboard'].values()))
def get_unit_delta(faction):
  nunits = len(filter(lambda x: x['piece'].split()[0] == faction, gamestate['gameboard'].values()))
  nsupplies = count_supply_centers(faction)
  return nsupplies - nunits
def get_home_territories(faction):
  return frozenset(filter(lambda x: starting_positions[x].split()[0] == faction, starting_positions))

#################### CONTROL ####################

def end_active_mode():
  resolve_orders()
  update_territories()
  show_board()
  create_retreat_orders()
  gamestate['mode'] = 'retreat'
  send_message_channel('Retreat!')
  send_message_channel(print_retreats())

def end_retreat_mode():
  resolve_retreat_orders()
  if gamestate['season'] == 'fall':
    gamestate['mode'] = 'adjustments'
    update_supply_ownership()
    show_board()
    for faction in FACTIONS:
      if count_supply_centers(faction) >= 18:
        gamestate['mode'] == 'pregame'
        send_message_channel("Game over! The winner is %s!!!" % faction)
        init_gamestate()
        return
    send_message_channel('Adjust units!')
    inform_adjustments()
  else:
    gamestate['mode'] = 'active'
    new_round()
def end_adjustments_mode():
  for faction in FACTIONS:
    delta = get_unit_delta(faction)
    if delta < 0:
      if faction not in gamestate['adjustments_orders'] or len(gamestate['adjustments_orders'][faction]['groups']) != -delta:
        send_message_channel("Cannot end because %s did not remove units!" % faction)
        return
  resolve_adjustments_orders()
  gamestate['mode'] = 'active'
  new_round()

def start_game():
  global gamestate
  empty_factions = filter(lambda x: len(gamestate['players'][x]) == 0, FACTIONS)
  if len(empty_factions) > 0:
    send_message_channel("These factions have no members: %s" % ", ".join(empty_factions))
  else:
    gamestate['mode'] = 'active'
    send_message_channel("@here Game on!!!")
    if 'season' in gamestate:
      del gamestate['season']
    if 'year' in gamestate:
      del gamestate['year']
    new_round()

def new_round():
  if 'season' not in gamestate or gamestate['season'] == 'fall':
    gamestate['season'] = 'spring'
    if 'year' not in gamestate:
      gamestate['year'] = 1901
    else:
      gamestate['year'] += 1
  else:
    gamestate['season'] = 'fall'
  send_message_channel("%s %d:" % (capitalize(gamestate['season']), gamestate['year']))
  show_board()
  ## Every piece holds by default
  gamestate['orders'] = {}
  for territory in filter(lambda x: gamestate['gameboard'][x]['piece'] != 'none', gamestate['gameboard']):
    add_order({'action': 'hold', 'territory': territory})
  gamestate['retreat_orders'] = {}
  gamestate['adjustments_orders'] = {}
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
          add_order({'territory': attacked_territory, 'action': 'hold', 'support': 0})
        elif order['support'] < attacked_territory_order['support']:
          add_order({'territory': territory, 'action': 'hold', 'support': 0})
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
    to = valid_retreat['to']
    piece = gamestate['dislodged_units'][territory][0]
    add_piece(piece, to)

def resolve_adjustments_orders():
  for order in gamestate['adjustments_orders'].values():
    faction = order['faction']
    groups = order['groups']
    if order['action'] == 'add':
      for unit, territory in groups:
        add_piece("%s %s" % (faction, unit), territory)
    elif order['action'] == 'remove':
      for _, territory in groups:
        remove_piece(territory)

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

def update_supply_ownership():
  for space in gamestate['gameboard'].values():
    if space['piece'] != 'none' and 'supply' in space and space['supply'] != 'none':
      space['supply'] = space['piece'].split()[0]

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
    if gamestate['gameboard'][space]['type'] == 'coastal':
      gamestate['gameboard'][space]['coastal_borders'] = frozenset(gamestate['gameboard'][space]['coastal_borders'])
  for pos in starting_positions:
    gamestate['gameboard'][pos]['piece'] = starting_positions[pos]
  gamestate['mode'] = 'pregame'
  
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
