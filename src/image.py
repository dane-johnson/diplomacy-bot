from PIL import Image

ARMY_SIZE = (20, 15)

_gameboard = Image.open('resources/gameboard.png')
_army = Image.open('resources/cannon.gif')

def get_gameboard():
  return _gameboard.copy()

def add_army(gameboard, coords):
  army = _army.resize(ARMY_SIZE)
  army_mask = army.convert('RGBA')
  gameboard.paste(army, coords, mask=army_mask)

def demo():
  gameboard = get_gameboard()
  add_army(gameboard, (40, 60))
  gameboard.show()

if __name__ == "__main__":
  demo()
