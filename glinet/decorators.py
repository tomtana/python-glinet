from functools import wraps
import glinet.exceptions as exceptions


def login_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        if not has_sid(self):
            raise exceptions.NotLoggedInError(f"Login is required to execute function {func}.\nCall login() first!")
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
