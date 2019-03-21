## To Run:
1. Set up a virtualenv environment `virtualenv ENV`
1. Activate the virtualenv environment `source ENV/bin/activate`
1. Install the requirements `pip install -r requirements.txt`
1. Create a `.env` file with the variables `APP_TOKEN=<your_app_token>` and `BOT_TOKEN=<your_bot_token>`
1. Select your interface, one of `cli`, `slack`, or `discord`
1. If using discord, install `node` and `npm`, and run `npm i`
1. Start the server `./bin/start`
