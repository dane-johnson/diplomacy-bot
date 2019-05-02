def group_by(coll, key):
  groupings = {}
  for val in coll:
    groupkey = val[key]
    if groupkey in groupings:
      groupings[groupkey].append(val)
    else:
      groupings[groupkey] = [val]
  return groupings.values()
