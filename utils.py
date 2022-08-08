from collections import namedtuple, OrderedDict


def create_recursive_object(obj, obj_name):
    if isinstance(obj, dict):
        fields = sorted(obj.keys())
        namedtuple_type = namedtuple(
            typename=obj_name,
            field_names=fields,
            rename=True,
        )
        field_value_pairs = OrderedDict(
            (str(field), create_recursive_object(obj[field], obj_name)) for field in fields)
        try:
            return namedtuple_type(**field_value_pairs)
        except TypeError:
            # Cannot create namedtuple instance so fallback to dict (invalid attribute names)
            return dict(**field_value_pairs)
    elif isinstance(obj, (list, set, tuple, frozenset)):
        return [create_recursive_object(item, obj_name) for item in obj]
    else:
        return obj
