from collections import namedtuple, OrderedDict
import re


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


class ResultContainer(dict):
    def __init__(self, name, data):
        self.name = name
        dict.__init__(self, data)
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return ResultContainer(self.name, value) if isinstance(value, dict) else value

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)



def sanitize_string(string):
    return re.sub(r"[,\-!/]", "_", string)
