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

