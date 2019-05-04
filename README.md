# User Info
First off, read the rules of diplomacy [here](https://web.archive.org/web/20190429013343/https://www.wizards.com/avalonhill/rules/diplomacy.pdf). The commands are split into two categories, public and private. Public commands are for actions outside of the game, like joining a team, looking at the board, and advancing the game. Public commands are issued in the public channel by mentioning the game master.  Private commands are those described in the game rules, like moving pieces and holding. Private commands are issued in a private chat with the game master.
## Vocab
- __[nation]__ One of england, france, germany, austria-hungary, italy, russia and turkey
- __[piece]__ One of fleet or army
- __[territory]__ One of the three letter spaces on the board
## Public Commands
- __register [nation]__ - Join the nation of your choice, must be done before the game starts
- __display factions__ - Show a list of which players are associated with each nation
- __display board__ - Show the gameboard
- __start__ - Begin the game
- __end__ - Advance the game by ending the current round. Be sure all orders have been placed before advancing.
- __amend [nation] ([piece] or remove) at [territory]__ - The game logic was hard to code and I probably made mistakes. Amend allows you to add and remove pieces to remedy mistakes. 
## Private Commands
- __[piece] [territory] holds__ - Order this piece not to move this turn, the default order for every piece.
- __[piece] [territory] to [territory]__ - Order this peice to move or attack a connected territory.
- __[piece] [territory] supports [piece] [territory] (to [territory])__ - Order this piece to give support to another piece.
- __fleet [territory] convoys army [territory] to [territory]__ - Order this fleet to convoy an army to a different space.
- __[piece] [territory] disbands__ - Order this dislodged piece to be removed from the board.
- __[piece] [territory] retreats to [territory]__ - Order this dislodged piece to retreat to a new territory.
# Development Blog
I made a number of mistakes on this project, particularly early on. The minimum viable product for this would have been me taking 
photos of the board and sending it over text. Fully automating the game logic for a game I have never played was a mistake, and I realized that each page of the 20 page instruction manual translated to about 100 lines of code.

Regardless, I'm looking ahead now, the new minimum product is simply the game logic, over Discord. I will not make another time estimation because I have been wrong so many times, so I will simply say _soon_. Ready yourselves for war.

I've put time into this, but it is untested and likely to have bugs. I will still be developing the game as it is being played, so expect changes, and refer to this document for updates.
# Developer Info
## To Run:
1. Set up a virtualenv environment `virtualenv ENV`
1. Activate the virtualenv environment `source ENV/bin/activate`
1. Install the requirements `pip install -r requirements.txt`
1. Create a `.env` file with the variables `APP_TOKEN=<your_app_token>` and `BOT_TOKEN=<your_bot_token>`
1. Select your interface, one of `cli`, `slack`, or `discord`
1. If using discord, install `node` and `npm`, and run `npm i`
1. Start the server `./bin/start`
