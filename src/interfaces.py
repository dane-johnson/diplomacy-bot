import os
import json
import requests

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
