from pandocfilters import (
    BulletList,
    CodeBlock,
    Div,
    Emph,
    Para,
    Plain,
    Str,
    Strong,
    RawBlock,
    stringify,
    toJSONFilters
)


def remove_collapse(key, value, format, meta):
    try:
        if key == "Div" and value[0][1] == ["collapse"]:
            return CodeBlock(*value[1][1].get("c"))
    except IndexError:
        return None


def convert_warning(key, value, format, meta):
    if key == "Div":
        [[identification, classes, keyvals], content] = value
        if classes in (["note"], ["warning"], ["tip"], ["important"], ["caution"]):
            alert_type = classes[0].upper()
            para = RawBlock("markdown", f"> [!{alert_type}]")
            result = []
            for item in content[1:]:
                if item["t"] == "BulletList":
                    for bullet in item["c"]:
                        # Stringify bullet and prepend "> - " for bullet lists
                        bullet_text = "> - " + " ".join(stringify(subitem) for subitem in bullet)
                        result.append(RawBlock("markdown", bullet_text))
                elif item["t"] == "Para":
                    # Stringify other elements and prepend "> "
                    text = "> " + "\n".join(stringify(item).splitlines()) + "\n"
                    result.append(RawBlock("markdown", text))
            # raise Exception([para] + result)
            return [para] + result



if __name__ == "__main__":
    toJSONFilters([remove_collapse, convert_warning])
