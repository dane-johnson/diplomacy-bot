import re

gameboard = {
  'nao': {'type': 'water', 'borders': ['nwg', 'cly', 'lvp', 'iri', 'mao']},
  'nwg': {'type': 'water', 'borders': ['bar', 'nwy', 'nth', 'edi', 'cly', 'nao']},
  'bar': {'type': 'water', 'borders': ['stp', 'nwy', 'nwg']},
  'stp': {'type': 'coastal', 'supply': 'russia', 'borders': ['bar', 'mos', 'lvn', 'bot', 'fin', 'nwy']},
  'mos': {'type': 'land', 'supply': 'russia', 'borders': ['stp', 'sev', 'ukr', 'war', 'lvn']},
  'sev': {'type': 'coastal', 'supply': 'russia', 'borders': ['mos', 'arm', 'bla', 'rum', 'ukr']},
  'arm': {'type': 'coastal', 'supply': 'none', 'borders': ['sev', 'syr', 'smy', 'ank', 'bla']},
  'syr': {'type': 'coastal', 'supply': 'none', 'borders': ['arm', 'eas', 'smy']},
  'eas': {'type': 'water', 'borders': ['smy', 'syr', 'ion', 'aeg']},
  'ion': {'type': 'water', 'borders': ['adr', 'alb', 'gre', 'aeg', 'eas', 'tun', 'tys', 'nap', 'apu']},
  'tun': {'type': 'coastal', 'supply': 'neutral', 'borders': ['tys', 'ion', 'naf', 'wes']},
  'naf': {'type': 'coastal', 'supply': 'none', 'borders': ['wes', 'tun', 'mao']},
  'mao': {'type': 'water', 'borders': ['nao', 'iri', 'eng', 'bre', 'gas', 'spa', 'por', 'wes', 'naf']},
  'iri': {'type': 'water', 'borders': ['nao', 'lvp', 'wal', 'eng', 'mao']},
  'lvp': {'type': 'coastal', 'supply': 'england', 'borders': ['cly', 'edi', 'yor', 'wal', 'iri', 'nao']},
  'cly': {'type': 'coastal', 'supply': 'none', 'borders': ['nao', 'nwg', 'edi', 'lvp']},
  'edi': {'type': 'coastal', 'supply': 'england', 'borders': ['nwg', 'nth', 'yor', 'lvp', 'cly']},
  'nth': {'type': 'water', 'borders': ['nwg', 'nwy', 'ska', 'den', 'hel', 'hol', 'bel', 'eng', 'lon', 'yor', 'edi']},
  'nwy': {'type': 'coastal', 'supply': 'neutral', 'borders': ['nwg', 'bar', 'stp', 'fin', 'swe', 'ska', 'nth']},
  'swe': {'type': 'coastal', 'supply': 'neutral', 'borders': ['nwy', 'fin', 'bot', 'bal', 'ska']},
  'fin': {'type': 'coastal', 'supply': 'none', 'borders': ['nwy', 'stp', 'bot', 'swe']},
  'bot': {'type': 'water', 'borders': ['swe', 'fin', 'stp', 'lvn', 'bal']},
  'lvn': {'type': 'coastal', 'supply': 'none', 'borders': ['bot', 'stp', 'mos', 'war', 'pru', 'bal']},
  'ukr': {'type': 'land', 'supply': 'none', 'borders': ['mos', 'sev', 'rum', 'gal', 'war']},
  'bla': {'type': 'water', 'borders': ['sev', 'arm', 'ank', 'con', 'bul', 'aeg', 'bul']},
  'ank': {'type': 'coastal', 'supply': 'turkey', 'borders': ['bla', 'arm', 'smy', 'con']},
  'smy': {'type': 'coastal', 'supply': 'turkey', 'borders': ['ank', 'arm', 'syr', 'eas', 'aeg', 'con']},
  'aeg': {'type': 'water', 'borders': ['bul', 'con', 'bla', 'smy', 'eas', 'ion', 'gre']},
  'gre': {'type': 'coastal', 'supply': 'neutral', 'borders': ['ser', 'bul', 'aeg', 'ion', 'adr', 'alb']},
  'nap': {'type': 'coastal', 'supply': 'italy', 'borders': ['apu', 'ion', 'tys', 'rom', 'ven']},
  'tys': {'type': 'water', 'borders': ['lyo', 'tus', 'rom', 'nap' , 'ion', 'tun', 'wes']},
  'wes': {'type': 'water', 'borders': ['lyo', 'tys', 'tun', 'naf', 'mao', 'spa']},
  'spa': {'type': 'coastal', 'supply': 'neutral', 'borders': ['mao', 'gas', 'mar', 'lyo', 'wes', 'por']},
  'por': {'type': 'coastal', 'supply': 'neutral', 'borders': ['mao', 'spa']},
  'gas': {'type': 'coastal', 'supply': 'none', 'borders': ['bre', 'par', 'bur', 'mar', 'spa', 'mao']},
  'bre': {'type': 'coastal', 'supply': 'france', 'borders': ['eng', 'pic', 'par', 'gas', 'mao']},
  'eng': {'type': 'water', 'borders': ['wal', 'lon', 'nth', 'bel', 'pic', 'bre', 'mao', 'iri']},
  'wal': {'type': 'coastal', 'supply': 'none', 'borders': ['lvp', 'yor', 'lon', 'eng', 'iri']}
}

def print_board_issues():
  for territory in gameboard:
    if not re.match(r"[a-z]{3}", territory):
      print "%s isn't a valid territory name" % territory
    for border in gameboard[territory]['borders']:
      if border not in gameboard:
        print "%s borders %s but %s isn't on the gameboard" % (territory, border, border)
      elif territory not in frozenset(gameboard[border]['borders']):
        print "%s borders %s but %s does not border %s" % (territory, border, border, territory)

if __name__ == "__main__":
  print_board_issues()
