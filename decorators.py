import logging
from functools import wraps
import exceptions


def login_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        if not has_sid(self):
            raise exceptions.NotLoggedInError(f"Login attempt unsuccessful. Login is required for function {func}.")
        return func(self, *args, **kwargs)

    return inner_func


def has_sid(func):
    try:
        if func.sid is None:
            return False
    except AttributeError:
        if func._session.sid is None:
            return False
    return True
