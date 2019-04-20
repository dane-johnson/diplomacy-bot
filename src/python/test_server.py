import unittest
import server

def create_event(type, text, user="no user", channel="no channel"):
  return {"type": type, "text": text, "user": user, "channel": channel}
def create_message(text, user="no user", channel="no channel"):
  return create_event("message", text, channel)
def create_app_mention(text, user="no user"):
  return create_event("app_mention", text, user, "diplomacy")

class ServerTest(unittest.TestCase):
  def setUp(self):
    server.init_gamestate()
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
if __name__ == "__main__":
  unittest.main()
