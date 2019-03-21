import json
from PIL import Image

ARMY_SIZE = (20, 15)
FLEET_SIZE = (20, 15)

GREEN = (0, 255, 0)
BLUE = (0, 102, 255)

_gameboard = Image.open('resources/gameboard.png')
_army = Image.open('resources/cannon.gif')
_fleet = Image.open('resources/boat.gif')

coord_file = open('resources/standard.json')
coords = json.load(coord_file)

faction_colors = {
  'england': (47, 5, 255),
  'france': (5, 240, 255),
  'germany': (255, 11, 206),
  'russia': (255, 176, 5),
  'austria-hungary': (255, 5, 5),
  'turkey': (255, 246, 5),
  'italy': (10, 255, 46)
}

def get_pos(space):
  return coords[space]

def get_gameboard():
  return _gameboard.copy()

def add_piece(gameboard, piece_name, space, faction):
  color = faction_colors[faction]
  piece = get_piece_color(piece_name, color)
  piece_mask = piece.convert('RGBA')
  coords = get_pos(space)
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

def draw_gameboard(gameboard):
  gameboard_image = get_gameboard()
  for space in gameboard:
    if gameboard[space]['piece'] == 'none':
      continue
    [faction, piece_name] = gameboard[space]['piece'].split()
    add_piece(gameboard_image, piece_name, space, faction)
  return gameboard_image

def demo():
  gameboard = get_gameboard()
  add_piece(gameboard, 'army', 'ank', 'russia')
  gameboard.show()

if __name__ == "__main__":
  demo()