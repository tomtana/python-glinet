from collections import namedtuple, OrderedDict
import re


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
