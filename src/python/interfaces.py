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
      handle_event(event)
      return "OK"

  def run():
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
