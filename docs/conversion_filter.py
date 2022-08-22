from pandocfilters import toJSONFilter, Emph, CodeBlock, toJSONFilters, Strong, BulletList, Div, Plain, Para, Str

def remove_collapse(key, value, format, meta):
  try:
    if key == 'Div' and value[0][1] == ["collapse"]:
      return CodeBlock(*value[1][1].get('c'))
  except IndexError:
    return None

def convert_warning(key, value, format, meta):
  if key == 'Div':
      [[identification, classes, keyvals], content] = value
      if classes == ["note"]:

        bl = content[1]
        para = Para([Strong([Str("Note:")])])
        #div = Div(["", ["note"], []], [note, bl])
        #raise IOError(bl)
        return [para, bl]
      if classes == ["warning"]:

        bl = content[1]
        para = Para([Strong([Str("Warning:")])])
        #div = Div(["", ["note"], []], [note, bl])
        #raise IOError(bl)
        return [para, bl]




if __name__ == "__main__":
  toJSONFilters([remove_collapse, convert_warning])