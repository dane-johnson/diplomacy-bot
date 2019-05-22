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
import json
import requests
from flask import Flask, request

SLACK_URL = "https://slack.com/api/chat.postMessage"
SLACK_IMG_URL = "https://slack.com/api/files.upload"
DISCORD_URL = "https://discordapp.com/api"

class Interface:
  @staticmethod
  def send_message_im(message, app_channel):
    raise NotImplementedError()
  @staticmethod
  def send_message_channel(message):
    raise NotImplementedError()
  @staticmethod
  def send_image_channel(image):
    raise NotImplementedError()

class CLIInterface(Interface):
  def __init__(self, handle_event):
    self.app = Flask(__name__)
    
    @self.app.route("/event", methods=['POST'])
    def cli_event():
      params = request.get_json()
      event = params['event']
      handle_event(event)
      return "OK"

  def run(self):
    self.app.run('0.0.0.0', port=8080)
    
  @classmethod
  def send_message_im(cls, message, app_channel):
    print 'IM-%s:%s' % (app_channel, message)

  @classmethod
  def send_message_channel(cls, message):
    print 'CHANNEL-MESSAGE:%s' % message

  @classmethod
  def send_image_channel(cls, image):
    image.show()

class SlackInterface(Interface):
  def __init__(self, handle_event):
    self.app = Flask(__name__)
    self.invalid_ts = []
    
    @self.app.route("/event", methods=['POST'])
    def slack_hook():
      params = request.get_json()
      print params
      if 'challenge' in params:
        return request.get_json()['challenge']
      event = params['event']
      if event['type'] == 'message' and 'subtype' in event and event['subtype'] == 'bot_message':
        ## Avoid infinite loop, ignore bot messages
        return "OK"
      ## Sometimes slack gets the same message twice, lets ignore those
      if event['ts'] in frozenset(self.invalid_ts):
        return "OK"
      else:
        self.add_invalid_ts(event['ts'])
      handle_event(event)
      return "OK"
  def add_invalid_ts(self, ts):
    if len(self.invalid_ts) > 10:
      self.invalid_ts.pop(0)
    self.invalid_ts.append(ts)

  def run(self):
    self.app.run('0.0.0.0', port=8080)

  @classmethod
  def send_message_im(cls, message, app_channel):
    headers = {
      "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
    }
    body = {
      "text": message,
      "channel": app_channel,
    }

    requests.post(SLACK_URL, data=body, headers=headers)

  @classmethod
  def send_message_channel(cls, message):
    headers = {
      "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
    }
    body = {
      "text": message,
      "channel": "#diplomacy"
    }

    r = requests.post(SLACK_URL, data=body, headers=headers)
    r.raise_for_status()

  @classmethod
  def send_image_channel(cls, image):
    image.save('/tmp/board.png')
    headers = {
      "Authorization": "Bearer %s" % os.environ["BOT_TOKEN"]
    }
    body = {
      "channels": "#diplomacy"
    }
    files = {"file": open('/tmp/board.png')}
    requests.post(SLACK_IMG_URL, data=body, headers=headers, files=files)

class DiscordInterface(Interface):
  def __init__(self, handle_event):
    self.app = Flask(__name__)
    
    @self.app.route("/event", methods=['POST'])
    def discord_event():
      params = request.get_json()
      event = params['event']
      handle_event(event)
      return "OK"

  def run(self):
    self.app.run('0.0.0.0', port=8080)
    
  @classmethod
  def send_message_channel(cls, message):
    headers = {
      "Authorization": "Bot %s" % os.environ['DISCORD_BOT_TOKEN'],
      "Content-Type": "application/json",
    }
    body = {
      'content': message
    }
    requests.post("%s/channels/%s/messages" % (DISCORD_URL, os.environ['DISCORD_CHANNEL_ID']), data=json.dumps(body), headers=headers)

  @classmethod
  def send_image_channel(cls, image):
    image.save('/tmp/board.png')
    headers = {
      "Authorization": "Bot %s" % os.environ['DISCORD_BOT_TOKEN'],
    }
    files = {"file": open('/tmp/board.png')}
    requests.post("%s/channels/%s/messages" % (DISCORD_URL, os.environ['DISCORD_CHANNEL_ID']), files=files, headers=headers)

  @classmethod
  def send_message_im(cls, message, app_channel):
    headers = {
      "Authorization": "Bot %s" % os.environ['DISCORD_BOT_TOKEN'],
      "Content-Type": "application/json",
    }
    body = {
      'content': message
    }
    requests.post("%s/channels/%s/messages" % (DISCORD_URL, app_channel), data=json.dumps(body), headers=headers)
