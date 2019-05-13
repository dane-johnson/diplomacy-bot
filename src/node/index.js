/* Diplomacy bot is a bot to play diplomacy on Slack and Discord
 * Copyright (C) 2019 Dane Johnson
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License 
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *  */

require('dotenv').config();
const axios = require('axios');
const Discord = require('discord.js');
client = new Discord.Client();

client.on('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on('message', message => {
  const data = {};
  if (message.channel.type === 'dm') {
    if (message.author === client.user) {
      // Ignore messages we created
      return;
    }
    data.type = 'message';
  } else {
    if (!message.isMentioned(client.user)) {
      // Ignore all messages not directed at the bot
      return;
    }
    data.type = 'app_mention';
  }
  data.channel = message.channel.id;
  data.text = message.content;
  data.user = message.author.id;
  // Send the data to our friendly server
  axios.post('http://localhost:8080/event', {
    event: data
  });
});

client.login(process.env['DISCORD_BOT_TOKEN']);

