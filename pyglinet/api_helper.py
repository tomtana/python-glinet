from tabulate import tabulate
import pyglinet.decorators as decorators

class GlInetApiCall:
    def __init__(self, data, session):
        self._session = session
        for name, value in data.items():
            setattr(self, name, self._wrap(value))
        self.__doc__ = f"\nAvailable parameters (?=optional):\n" + self.__repr__() + f"\n\nExample request:\n{self.in_example}\n\n" + f"\n\nExample response:\n{self.out_example}\n"

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return GlInetApiProperty(value) if isinstance(value, dict) else value

    def call(self):
        self.__call__()

    @decorators.login_required
    def __call__(self, params=None):

        p = []
        if params:
            p = list(params)
        p = self.module_name + [self.data.title] + p
        return self._session.request("call", p).result

    def __repr__(self):
        return tabulate([[i.keyName, i.dataType__name, i.desp] for i in self.params],
                        headers=["Parameter", "Type", "Description"])

    def __str__(self):
        self.__repr__()


class GlInetApiProperty:
    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return GlInetApiProperty(value, self._session) if isinstance(value, dict) else value

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class GlInetApi:
    def __init__(self, data, session):
        self._session = session
        if data.get("case_groups_data", None):
            for name, value in data.get("case_groups_data").items():
                setattr(self, name, GlInetApiCall(value, self._session))
        else:
            for name, value in data.items():
                setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return GlInetApi(value, self._session) if isinstance(value, dict) else value

    def __repr__(self):
        return tabulate([[i] for i in list(self.__dict__.keys()) if not i.startswith("_")], headers=["Function"])

    def __str__(self):
        return str(self.__dict__)