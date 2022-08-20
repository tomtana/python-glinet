from functools import wraps
import pyglinet.exceptions as exceptions


def login_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        if _has_sid(self) and _is_alive(self):
            return func(self, *args, **kwargs)
        else:
            raise exceptions.NotLoggedInError(f"Login is required to execute function {func}.\nCall login() first!")

    return inner_func


def logout_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        try:
            if _is_alive(self):
                raise exceptions.LoggedInError(f"Logout before calling function {func}")
        except exceptions.NotLoggedInError:
            pass

        return func(self, *args, **kwargs)

    return inner_func


def _has_sid(func):
    try:
        if func._sid is None:
            return False
    except AttributeError:
        if func._session._sid is None:
            return False
    return True


def _is_alive(func):
    try:
        return func.is_alive()
    except AttributeError:
        return func._session.is_alive()
