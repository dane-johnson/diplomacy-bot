import unittest
import server
import gameboard
def create_event(type, text, user="no user", channel="no channel"):
  return {"type": type, "text": text, "user": user, "channel": channel}
def create_message(text, user="no user", channel="no channel"):
  return create_event("message", text, channel)
def create_app_mention(text, user="no user"):
  return create_event("app_mention", text, user, "diplomacy")

class ServerTest(unittest.TestCase):
  def setUp(self):
    server.init_gamestate()
  def tearDown(self):
    server.gamestate = {
      "players": {},
      "units": {},
      "orders": {},
      "mode": "pregame",
      "gameboard": gameboard.gameboard,
      "dislodged_units": {},
      "invalid_retreats": set([]),
      "retreat_orders": {}
    }
  def test_parse_order(self):
    self.assertEqual(
      server.parse_order("army abc holds"),
      {"action": "hold", "territory": "abc"})
    self.assertEqual(
      server.parse_order("army abc to bcd"),
      {"action": "move/attack", "territory": "abc", "to": "bcd"})
    self.assertEqual(
      server.parse_order("army abc supports army bcd to cde"),
      {"action": "support", "territory": "abc", "supporting": "bcd", "to": "cde"})
    self.assertEqual(
      server.parse_order("army abc supports army bcd"),
      {"action": "support", "territory": "abc", "supporting": "bcd"},)
    self.assertEqual(
      server.parse_order("fleet abc convoys army bcd to cde"),
      {"action": "convoy", "territory": "abc", "from": "bcd", "to": "cde"})
    self.assertEqual(
      server.parse_order("army abc retreats to bcd"),
      {"action": "retreat", "territory": "abc", "to": "bcd"})
    self.assertEqual(
      server.parse_order("army abc disbands"),
      {"action": "disband", "territory": "abc"})
  def test_add_order(self):
    hold_order = {"action": "hold", "territory": "abc"}
    attack_order = {"action": "move/attack", "territory": "abc", "to": "bcd"}
    server.gamestate['orders'] = {}
    server.add_order(hold_order)
    self.assertEqual(server.gamestate['orders'], {"abc": hold_order})
    server.add_order(attack_order)
    self.assertEqual(server.gamestate['orders'], {"abc": attack_order})
  def test_get_unit_delta_gain(self):
    server.gamestate['gameboard'] = {"abc": {"type": "land", "supply": "england", "piece": "none"}}
    self.assertEqual(server.get_unit_delta('england'), 1)
  def test_get_unit_delta_zero(self):
    server.gamestate['gameboard'] = {"abc": {"type": "land", "supply": "none", "piece": "england army"}}
    self.assertEqual(server.get_unit_delta('england'), -1)
    
  def test_order_error(self):
    server.gamestate['gameboard'] = {"abc": {"type": "land", "borders": []},
                                     "xyz": {"type": "land", "borders": []}}
    self.assertEqual(
      server.order_error({"action": "hold", "territory": "bcd"}, "england"),
      "Territory bcd is not valid"
    )
    self.assertEqual(
      server.order_error({"action": "move/attack", "territory": "abc", "to": "bcd"}, "england"),
      "Territory bcd is not valid"
    )
    self.assertEqual(
      server.order_error({"action": "support", "territory": "abc", "supporting": "bcd"}, "england"),
      "Territory bcd is not valid"
    )
    self.assertEqual(
      server.order_error({"action": "convoy", "territory": "abc", "from": "bcd", "to": "xyz"}, "england"),
      "Territory bcd is not valid"
    )

  def test_resolve_order_illegal_convoy(self):
    server.gamestate['gameboard'] = {"ion" : {"type": "water", "borders": set([]), "piece": "russia fleet"},
                                     "bud" : {"type": "land", "borders": set(["gal"]), "piece": "russia army"},
                                     "gal" : {"type": "land", "borders": set(["bud"])}}
    server.add_order({"territory": "ion", "action": "convoy", "from": "bud", "to": "gal"})
    server.add_order({"territory": "bud", "action": "move/attack", "to": "gal"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['bud']['is_convoyed'], False)

  def test_resolve_order_swap_standoff_equal(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos"]), "piece": "germany army"}}
    server.add_order({"territory": "stp", "action": "move/attack", "to": "mos"})
    server.add_order({"territory": "mos", "action": "move/attack", "to": "stp"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['stp']['action'], 'hold')
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'hold')
    
  def test_resolve_order_swap_standoff_unequal(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp", "lvn"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos", "lvn"]), "piece": "germany army"},
                                     "lvn": {"type": "land", "borders": set(["mos", "stp"]), "piece": "russia army"}}
    server.add_order({"territory": "stp", "action": "move/attack", "to": "mos"})
    server.add_order({"territory": "mos", "action": "move/attack", "to": "stp"})
    server.add_order({"territory": "lvn", "action": "support", "supporting": "mos", "to": "stp"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'move/attack')
    self.assertNotIn('stp', server.gamestate['orders'])
    self.assertEqual(server.gamestate['gameboard']['stp']['piece'], 'none')
    self.assertEqual(server.gamestate['dislodged_units']['stp'], ("germany army", "mos"))

  def test_resolve_order_swap_standoff_equal_convoyed(self):
    server.gamestate['gameboard'] = {"swe": {"type": "coastal", "borders": set(["fin", "bot"]), "piece": "russia army"},
                                     "fin": {"type": "coastal", "borders": set(["swe", "bot"]), "piece": "germany army"},
                                     "bot": {"type": "water", "borders": set(["swe", "fin"]), "piece": "germany fleet"}}
    server.add_order({"territory": "swe", "action": "move/attack", "to": "fin"})
    server.add_order({"territory": "fin", "action": "move/attack", "to": "swe"})
    server.add_order({"territory": "bot", "action": "convoy", "from": "fin", "to": "swe"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['swe']['action'], 'move/attack')
    self.assertEqual(server.gamestate['orders']['fin']['action'], 'move/attack')

  def test_resolve_order_move_move_equal_standoff(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp", "lvn"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos", "lvn"]), "piece": "none"},
                                     "lvn": {"type": "land", "borders": set(["mos", "stp"]), "piece": "germany army"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "stp"})
    server.add_order({"territory": "lvn", "action": "move/attack", "to": "stp"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'hold')
    self.assertEqual(server.gamestate['orders']['lvn']['action'], 'hold')
    self.assertIn('stp', server.gamestate['invalid_retreats'])
  def test_resolve_order_move_move_unequal_standoff(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp", "lvn", "fin"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos", "lvn", "fin"]), "piece": "none"},
                                     "lvn": {"type": "land", "borders": set(["mos", "stp", "fin"]), "piece": "germany army"},
                                     "fin": {"type": "land", "borders": set(["mos", "stp", "lvn"]), "piece": "russia army"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "stp"})
    server.add_order({"territory": "lvn", "action": "move/attack", "to": "stp"})
    server.add_order({"territory": "fin", "action": "support", "supporting": "mos", "to": "stp"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'move/attack')
    self.assertEqual(server.gamestate['orders']['lvn']['action'], 'hold')
    self.assertNotIn('stp', server.gamestate['invalid_retreats'])
  def test_resolve_order_move_hold_equal_standoff(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["lvn"]), "piece": "russia army"},
                                     "lvn": {"type": "land", "borders": set(["mos"]), "piece": "germany army"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "lvn"})
    server.add_order({"territory": "lvn", "action": "hold"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'hold')
    self.assertNotIn('lvn', server.gamestate['dislodged_units'])
  def test_resolve_order_move_hold_move_favored_standoff(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["lvn", "fin"]), "piece": "russia army"},
                                     "lvn": {"type": "land", "borders": set(["mos", "fin"]), "piece": "germany army"},
                                     "fin": {"type": "land", "borders": set(["mos", "lvn"]), "piece": "russia army"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "lvn"})
    server.add_order({"territory": "lvn", "action": "hold"})
    server.add_order({"territory": "fin", "action": "support", "supporting": "mos", "to": "lvn"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'move/attack')
    self.assertEqual(server.gamestate['dislodged_units']['lvn'], ('germany army', 'mos'))
    self.assertNotIn('lvn', server.gamestate['orders'])
  def test_resolve_order_traffic_backup_hold_favored_standoff(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp", "lvn", "fin"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos", "lvn", "fin"]), "piece": "france army"},
                                     "lvn": {"type": "land", "borders": set(["mos", "stp", "fin"]), "piece": "germany army"},
                                     "fin": {"type": "land", "borders": set(["mos", "stp", "lvn"]), "piece": "russia army"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "lvn"})
    server.add_order({"territory": "stp", "action": "hold"})
    server.add_order({"territory": "fin", "action": "support", "supporting": "mos", "to": "lvn"})
    server.add_order({"territory": "lvn", "action": "move/attack", "to": "stp"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'move/attack')
    self.assertEqual(server.gamestate['dislodged_units']['lvn'], ('germany army', 'mos'))
    self.assertEqual(server.gamestate['orders']['stp']['action'], 'hold' )
    self.assertNotIn('lvn', server.gamestate['orders'])
  def test_resolve_order_traffic_backup_attack_favored_standoff(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp", "lvn", "fin"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos", "lvn", "fin"]), "piece": "france army"},
                                     "lvn": {"type": "land", "borders": set(["mos", "stp", "fin"]), "piece": "germany army"},
                                     "fin": {"type": "land", "borders": set(["mos", "stp", "lvn"]), "piece": "russia army"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "lvn"})
    server.add_order({"territory": "stp", "action": "hold"})
    server.add_order({"territory": "fin", "action": "support", "supporting": "lvn", "to": "stp"})
    server.add_order({"territory": "lvn", "action": "move/attack", "to": "stp"})
    server.resolve_orders()
    self.assertEqual(server.gamestate['orders']['mos']['action'], 'move/attack')
    self.assertEqual(server.gamestate['dislodged_units']['stp'], ('france army', 'lvn'))
    self.assertEqual(server.gamestate['orders']['lvn']['action'], 'move/attack')
    self.assertNotIn('stp', server.gamestate['orders'])
  def test_update_territories(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["lvn"]), "piece": "russia army"},
                                     "lvn": {"type": "land", "borders": set(["mos"]), "piece": "none"}}
    server.add_order({"territory": "mos", "action": "move/attack", "to": "lvn"})
    server.update_territories()
    self.assertEqual(server.gamestate['gameboard']['lvn']['piece'], 'russia army')
    self.assertEqual(server.gamestate['gameboard']['mos']['piece'], 'none')
  def test_resolve_retreat_orders_no_conflicts(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["lvn", "fin"]), "piece": "russia army"},
                                     "lvn": {"type": "land", "borders": set(["mos", "fin"]), "piece": "none"},
                                     "fin": {"type": "land", "borders": set(["mos", "lvn"]), "piece": "none"}}
    server.gamestate['dislodged_units'] = {"lvn": ("germany army", "mos")}
    server.add_retreat_order({'territory': 'lvn', 'action': 'retreat', 'to': 'fin'})
    server.resolve_retreat_orders()
    self.assertEqual(server.gamestate['gameboard']['fin']['piece'], 'germany army')
  def test_resolve_retreat_orders_conflict(self):
    server.gamestate['gameboard'] = {"mos": {"type": "land", "borders": set(["stp", "lvn", "fin", "pru"]), "piece": "russia army"},
                                     "stp": {"type": "land", "borders": set(["mos", "lvn", "fin", "pru"]), "piece": "none"},
                                     "lvn": {"type": "land", "borders": set(["mos", "stp", "fin", "pru"]), "piece": "none"},
                                     "fin": {"type": "land", "borders": set(["mos", "stp", "lvn", "pru"]), "piece": "none"},
                                     "pru": {"type": "land", "borders": set(["mos", "stp", "lvn", "fin"]), "piece": "russia army"}}
    server.gamestate['dislodged_units'] = {"lvn": ("germany army", "mos"),
                                           "stp": ("france army", "pru")}
    server.add_retreat_order({'territory': 'lvn', 'action': 'retreat', 'to': 'fin'})
    server.add_retreat_order({'territory': 'stp', 'action': 'retreat', 'to': 'fin'})
    server.resolve_retreat_orders()
    self.assertEqual(server.gamestate['gameboard']['fin']['piece'], 'none')
if __name__ == "__main__":
  unittest.main()
