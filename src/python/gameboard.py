# Diplomacy bot is a bot to play diplomacy on Slack and Discord
# Copyright (C) 2019 Dane Johnson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License 
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re

gameboard = {
  'nat': {'type': 'water', 'borders': ['nrg', 'cly', 'lvp', 'iri', 'mid']},
  'nrg': {'type': 'water', 'borders': ['bar', 'nwy', 'nth', 'edi', 'cly', 'nat']},
  'bar': {'type': 'water', 'borders': ['stp', 'nwy', 'nrg']},
  'stp': {'type': 'coastal', 'supply': 'russia', 'borders': ['bar', 'mos', 'lvn', 'bot', 'fin', 'nwy'], 'coastal_borders': ['fin', 'lvn', 'nwy']},
  'mos': {'type': 'land', 'supply': 'russia', 'borders': ['stp', 'sev', 'ukr', 'war', 'lvn']},
  'sev': {'type': 'coastal', 'supply': 'russia', 'borders': ['mos', 'arm', 'bla', 'rum', 'ukr'], 'coastal_borders': ['rum', 'arm']},
  'arm': {'type': 'coastal', 'supply': 'none', 'borders': ['sev', 'syr', 'smy', 'ank', 'bla'], 'coastal_borders': ['sev', 'ank']},
  'syr': {'type': 'coastal', 'supply': 'none', 'borders': ['arm', 'eas', 'smy'], 'coastal_borders': ['smy']},
  'eas': {'type': 'water', 'borders': ['smy', 'syr', 'ion', 'aeg']},
  'ion': {'type': 'water', 'borders': ['adr', 'alb', 'gre', 'aeg', 'eas', 'tun', 'tyn', 'nap', 'apu']},
  'tun': {'type': 'coastal', 'supply': 'neutral', 'borders': ['tyn', 'ion', 'naf', 'wes'], 'coastal_borders': ['naf']},
  'naf': {'type': 'coastal', 'supply': 'none', 'borders': ['wes', 'tun', 'mid'], 'coastal_borders': ['tun']},
  'mid': {'type': 'water', 'borders': ['nat', 'iri', 'eng', 'bre', 'gas', 'spa', 'por', 'wes', 'naf']},
  'iri': {'type': 'water', 'borders': ['nat', 'lvp', 'wal', 'eng', 'mid']},
  'lvp': {'type': 'coastal', 'supply': 'england', 'borders': ['cly', 'edi', 'yor', 'wal', 'iri', 'nat'], 'coastal_borders': ['cly', 'wal']},
  'cly': {'type': 'coastal', 'supply': 'none', 'borders': ['nat', 'nrg', 'edi', 'lvp'], 'coastal_borders': ['lvp', 'edi']},
  'edi': {'type': 'coastal', 'supply': 'england', 'borders': ['nrg', 'nth', 'yor', 'lvp', 'cly'], 'coastal_borders': ['cly', 'yor']},
  'nth': {'type': 'water', 'borders': ['nrg', 'nwy', 'ska', 'den', 'hel', 'hol', 'bel', 'eng', 'lon', 'yor', 'edi']},
  'nwy': {'type': 'coastal', 'supply': 'neutral', 'borders': ['nrg', 'bar', 'stp', 'fin', 'swe', 'ska', 'nth'], 'coastal_borders': ['stp', 'swe']},
  'swe': {'type': 'coastal', 'supply': 'neutral', 'borders': ['nwy', 'fin', 'bot', 'bal', 'den', 'ska'], 'coastal_borders': ['nwy', 'fin']},
  'fin': {'type': 'coastal', 'supply': 'none', 'borders': ['nwy', 'stp', 'bot', 'swe'], 'coastal_borders': ['swe', 'stp']},
  'bot': {'type': 'water', 'borders': ['swe', 'fin', 'stp', 'lvn', 'bal']},
  'bal': {'type': 'water', 'borders': ['bot', 'lvn', 'pru', 'ber', 'kie', 'hel', 'den', 'ska', 'swe']},
  'lvn': {'type': 'coastal', 'supply': 'none', 'borders': ['bot', 'stp', 'mos', 'war', 'pru', 'bal'], 'coastal_borders': ['stp', 'pru']},
  'ukr': {'type': 'land', 'supply': 'none', 'borders': ['mos', 'sev', 'rum', 'gal', 'war']},
  'bla': {'type': 'water', 'borders': ['sev', 'arm', 'ank', 'con', 'bul', 'aeg', 'bul', 'rum']},
  'ank': {'type': 'coastal', 'supply': 'turkey', 'borders': ['bla', 'arm', 'smy', 'con'], 'coastal_borders': ['arm', 'con']},
  'smy': {'type': 'coastal', 'supply': 'turkey', 'borders': ['ank', 'arm', 'syr', 'eas', 'aeg', 'con'], 'coastal_borders': ['syr', 'con']},
  'aeg': {'type': 'water', 'borders': ['bul', 'con', 'bla', 'smy', 'eas', 'ion', 'gre']},
  'gre': {'type': 'coastal', 'supply': 'neutral', 'borders': ['ser', 'bul', 'aeg', 'ion', 'alb'], 'coastal_borders': ['bul', 'alb']},
  'apu': {'type': 'coastal', 'supply': 'none', 'borders': ['adr', 'ion', 'nap', 'rom', 'ven'], 'coastal_borders': ['ven', 'nap']},
  'nap': {'type': 'coastal', 'supply': 'italy', 'borders': ['apu', 'ion', 'tyn', 'rom'], 'coastal_borders': ['apu', 'rom']},
  'tyn': {'type': 'water', 'borders': ['gol', 'tus', 'rom', 'nap' , 'ion', 'tun', 'wes']},
  'wes': {'type': 'water', 'borders': ['gol', 'tyn', 'tun', 'naf', 'mid', 'spa']},
  'spa': {'type': 'coastal', 'supply': 'neutral', 'borders': ['mid', 'gas', 'mar', 'gol', 'wes', 'por'], 'coastal_borders': ['gas', 'por', 'mar']},
  'por': {'type': 'coastal', 'supply': 'neutral', 'borders': ['mid', 'spa'], 'coastal_borders': ['spa']},
  'gas': {'type': 'coastal', 'supply': 'none', 'borders': ['bre', 'par', 'bur', 'mar', 'spa', 'mid'], 'coastal_borders': ['bre', 'spa']},
  'bre': {'type': 'coastal', 'supply': 'france', 'borders': ['eng', 'pic', 'par', 'gas', 'mid'], 'coastal_borders': ['gas', 'pic']},
  'eng': {'type': 'water', 'borders': ['wal', 'lon', 'nth', 'bel', 'pic', 'bre', 'mid', 'iri']},
  'wal': {'type': 'coastal', 'supply': 'none', 'borders': ['lvp', 'yor', 'lon', 'eng', 'iri'], 'coastal_borders': ['lvp', 'lon']},
  'yor': {'type': 'coastal', 'supply': 'none', 'borders': ['edi', 'nth', 'lon', 'wal', 'lvp'], 'coastal_borders': ['lon', 'edi']},
  'ska': {'type': 'water', 'borders': ['nwy', 'swe', 'bal', 'den', 'nth']},
  'pru': {'type': 'coastal', 'supply': 'none', 'borders': ['bal', 'lvn', 'war', 'sil', 'ber'], 'coastal_borders': ['ber', 'lvn']},
  'war': {'type': 'land', 'supply': 'russia', 'borders': ['pru', 'lvn', 'mos', 'ukr', 'gal', 'sil']},
  'gal': {'type': 'land', 'supply': 'none', 'borders': ['war', 'ukr', 'rum', 'bud', 'vie', 'boh', 'sil']},
  'rum': {'type': 'coastal', 'supply': 'neutral', 'borders': ['ukr', 'sev', 'bla', 'bul', 'ser', 'bud', 'gal'], 'coastal_borders': ['sev', 'bul']},
  'con': {'type': 'coastal', 'supply': 'turkey', 'borders': ['bla', 'ank', 'smy', 'aeg', 'bul'], 'coastal_borders': ['ank', 'smy', 'bul']},
  'bul': {'type': 'coastal', 'supply': 'neutral', 'borders': ['rum', 'bla', 'con', 'aeg', 'gre', 'ser'], 'coastal_borders': ['rum', 'con', 'gre']},
  'ser': {'type': 'land', 'supply': 'neutral', 'borders': ['bud', 'rum', 'bul', 'gre', 'alb', 'tri']},
  'alb': {'type': 'coastal', 'supply': 'none', 'borders': ['ser', 'gre', 'ion', 'adr', 'tri'], 'coastal_borders': ['gre', 'tri']},
  'adr': {'type': 'water', 'borders': ['tri', 'alb', 'ion', 'apu', 'ven']},
  'rom': {'type': 'coastal', 'supply': 'italy', 'borders': ['tus', 'ven', 'apu', 'nap', 'tyn'], 'coastal_borders': ['tus', 'nap']},
  'gol': {'type': 'water', 'borders': ['mar', 'pie', 'tus', 'tyn', 'wes', 'spa']},
  'mar': {'type': 'coastal', 'supply': 'france', 'borders': ['bur', 'pie', 'gol', 'spa', 'gas'], 'coastal_borders': ['pie', 'spa']},
  'bur': {'type': 'land', 'supply': 'none', 'borders': ['bel', 'ruh', 'mun', 'mar', 'gas', 'par', 'pic']},
  'par': {'type': 'land', 'supply': 'france', 'borders': ['pic', 'bur', 'gas', 'bre']},
  'pic': {'type': 'coastal', 'supply': 'none', 'borders': ['bel', 'bur', 'par', 'bre', 'eng'], 'coastal_borders': ['bre', 'bel']},
  'bel': {'type': 'coastal', 'supply': 'neutral', 'borders': ['nth', 'hol', 'ruh', 'bur', 'pic', 'eng'], 'coastal_borders': ['pic', 'hol']},
  'lon': {'type': 'coastal', 'supply': 'england', 'borders': ['yor', 'nth', 'eng', 'wal'], 'coastal_borders': ['yor', 'wal']},
  'hol': {'type': 'coastal', 'supply': 'neutral', 'borders': ['hel', 'kie', 'ruh', 'bel', 'nth'], 'coastal_borders': ['bel', 'kie']},
  'hel': {'type': 'water', 'borders': ['nth', 'den', 'bal', 'kie', 'hol']},
  'den': {'type': 'coastal', 'supply': 'neutral', 'borders': ['ska', 'swe', 'kie', 'bal', 'hel', 'nth'], 'coastal_borders': ['kie']},
  'ska': {'type': 'water', 'borders': ['nwy', 'swe', 'den', 'bal', 'nth']},
  'ber': {'type': 'coastal', 'supply': 'germany', 'borders': ['bal', 'pru', 'sil', 'mun', 'kie'], 'coastal_borders': ['kie', 'pru']},
  'sil': {'type': 'land', 'supply': 'none', 'borders': ['pru', 'war', 'gal', 'boh', 'mun', 'ber']},
  'bud': {'type': 'land', 'supply': 'austria-hungary', 'borders': ['gal', 'rum', 'ser', 'tri', 'vie']},
  'tri': {'type': 'coastal', 'supply': 'austria-hungary', 'borders': ['vie', 'bud', 'ser', 'alb', 'adr', 'ven', 'tyr'], 'coastal_borders': ['ven', 'alb']},
  'ven': {'type': 'coastal', 'supply': 'italy', 'borders': ['tyr', 'tri', 'adr', 'apu', 'rom', 'tus', 'pie'], 'coastal_borders': ['tri', 'apu']},
  'tus': {'type': 'coastal', 'supply': 'none', 'borders': ['ven', 'rom', 'tyn', 'gol', 'pie'], 'coastal_borders': ['pie', 'rom']},
  'pie': {'type': 'coastal', 'supply': 'none', 'borders': ['tyr', 'ven', 'tus', 'gol', 'mar'], 'coastal_borders': ['mar', 'tus']},
  'mun': {'type': 'land', 'supply': 'germany', 'borders': ['ber', 'sil', 'boh', 'tyr', 'bur', 'ruh', 'kie']},
  'ruh': {'type': 'land', 'supply': 'none', 'borders': ['kie', 'mun', 'bur', 'bel', 'hol']},
  'kie': {'type': 'coastal', 'supply': 'germany', 'borders': ['den', 'bal', 'ber', 'mun', 'ruh', 'hol', 'hel'], 'coastal_borders': ['hol', 'den', 'ber']},
  'boh': {'type': 'land', 'supply': 'none', 'borders': ['sil', 'gal', 'vie', 'tyr', 'mun']},
  'vie': {'type': 'land', 'supply': 'austria-hungary', 'borders': ['gal', 'bud', 'tri', 'tyr', 'boh']},
  'tyr': {'type': 'land', 'supply': 'none', 'borders': ['boh', 'vie', 'tri', 'ven', 'pie', 'mun']},
}

starting_positions = {
  'vie': 'austria-hungary army',
  'bud': 'austria-hungary army',
  'tri': 'austria-hungary fleet',
  'lon': 'england fleet',
  'edi': 'england fleet',
  'lvp': 'england army',
  'par': 'france army',
  'mar': 'france army',
  'bre': 'france fleet',
  'ber': 'germany army',
  'mun': 'germany army',
  'kie': 'germany fleet',
  'rom': 'italy army',
  'ven': 'italy army',
  'nap': 'italy fleet',
  'mos': 'russia army',
  'sev': 'russia fleet',
  'war': 'russia army',
  'stp': 'russia fleet',
  'ank': 'turkey fleet',
  'con': 'turkey army',
  'smy': 'turkey army'
}

def print_board_issues():
  for territory in gameboard:
    if not re.match(r"[a-z]{3}", territory):
      print "%s isn't a valid territory name" % territory
    if not 'type' in gameboard[territory] or gameboard[territory]['type'] not in frozenset(['land', 'water', 'coastal']):
      print "%s has an incorrect type" % territory
      continue
    if gameboard[territory]['type'] in frozenset(['land', 'coastal']) and 'supply' not in gameboard[territory]:
      print "%s has an incorrect supply" % territory
    if 'borders' not in gameboard[territory]:
      print "%s missing borders" % territory
      continue
    for border in gameboard[territory]['borders']:
      if border not in gameboard:
        print "%s borders %s but %s isn't on the gameboard" % (territory, border, border)
      elif territory not in frozenset(gameboard[border]['borders']):
        print "%s borders %s but %s does not border %s" % (territory, border, border, territory)
    if gameboard[territory]['type'] == 'coastal':
      if 'coastal_borders' not in gameboard[territory]:
        print "%s missing coastal_borders" % territory
        continue
      for coastal_border in gameboard[territory]['coastal_borders']:
        if gameboard[coastal_border]['type'] != 'coastal':
          print "%s coastal boarders %s but %s is type %s" % (territory, coastal_border, coastal_border, gameboard[coastal_border]['type'])
        elif territory not in frozenset(gameboard[coastal_border]['coastal_borders']):
          print "%s coastal boarders %s but %s does not coastal border %s" % (territory, coastal_border, coastal_border, territory)
  supply_centers = filter(lambda x: gameboard[x]['type'] != 'water' and gameboard[x]['supply'] != 'none', gameboard)
  if len(supply_centers) != 34:
    print 'There are not the correct amount of supply centers (%d/34)' % len(supply_centers)

if __name__ == "__main__":
  print_board_issues()
