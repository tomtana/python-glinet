from functools import wraps
import pyglinet.exceptions as exceptions


def login_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        if not has_sid(self):
            raise exceptions.NotLoggedInError(f"Login is required to execute function {func}.\nCall login() first!")
        return func(self, *args, **kwargs)

    return inner_func

def logout_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        try:
            if self.is_alive():
                raise exceptions.LoggedInError("Logout before calling login again.")
        except exceptions.NotLoggedInError:
            pass

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
