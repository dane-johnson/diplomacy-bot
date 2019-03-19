require('dotenv').config();
const axios = require('axios');
const Discord = require('discord.js');
client = new Discord.Client();

client.on('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.login(process.env['DISCORD_BOT_TOKEN']);

