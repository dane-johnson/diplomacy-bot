from PIL import Image

ARMY_SIZE = (20, 15)

GREEN = (0, 255, 0)
BLUE = (0, 102, 255)

_gameboard = Image.open('resources/gameboard.png')
_army = Image.open('resources/cannon.gif')

def get_gameboard():
  return _gameboard.copy()

def add_army(gameboard, coords, color):
  army = get_army_color(color)
  army_mask = army.convert('RGBA')
  gameboard.paste(army, coords, mask=army_mask)

def get_army_color(rgb):
  r, g, b = rgb
  army = _army.resize(ARMY_SIZE).convert('RGBA')
  pixels = army.load()
  for y in xrange(army.size[1]):
    for x in xrange(army.size[0]):
      if pixels[x, y] == (255, 255, 255, 255):
        pixels[x, y] = (r, g, b, 255)
  return army

def demo():
  gameboard = get_gameboard()
  add_army(gameboard, (40, 60), BLUE)
  gameboard.show()

if __name__ == "__main__":
  demo()
