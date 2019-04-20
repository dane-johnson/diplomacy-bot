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
      "dislodged_units": {}
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
  def test_add_order(self):
    hold_order = {"action": "hold", "territory": "abc"}
    attack_order = {"action": "move/attack", "territory": "abc", "to": "bcd"}
    server.gamestate['orders'] = {}
    server.add_order(hold_order)
    self.assertEqual(server.gamestate['orders'], {"abc": hold_order})
    server.add_order(attack_order)
    self.assertEqual(server.gamestate['orders'], {"abc": attack_order})
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
    


if __name__ == "__main__":
  unittest.main()
