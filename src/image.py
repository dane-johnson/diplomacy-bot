from PIL import Image

ARMY_SIZE = (20, 15)
FLEET_SIZE = (20, 15)

GREEN = (0, 255, 0)
BLUE = (0, 102, 255)

_gameboard = Image.open('resources/gameboard.png')
_army = Image.open('resources/cannon.gif')
_fleet = Image.open('resources/boat.gif')

def get_gameboard():
  return _gameboard.copy()

def add_piece(gameboard, piece_name, coords, color):
  piece = get_piece_color(piece_name, color)
  piece_mask = piece.convert('RGBA')
  gameboard.paste(piece, coords, mask=piece_mask)

def get_piece_color(piece_name, rgb):
  r, g, b = rgb
  if piece_name == 'army':
    piece = _army.resize(ARMY_SIZE).convert('RGBA')
  else:
    piece = _fleet.resize(FLEET_SIZE).convert('RGBA')
  pixels = piece.load()
  for y in xrange(piece.size[1]):
    for x in xrange(piece.size[0]):
      if pixels[x, y] == (255, 255, 255, 255):
        pixels[x, y] = (r, g, b, 255)
  return piece

def demo():
  gameboard = get_gameboard()
  add_piece(gameboard, 'fleet', (40, 60), BLUE)
  gameboard.show()

if __name__ == "__main__":
  demo()
