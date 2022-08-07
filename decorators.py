from functools import wraps
import exceptions


def login_required(func):
    @wraps(func)
    def inner_func(self, *args, **kwargs):
        if self.sid is None:
            raise exceptions.NotLoggedInError(f"Login is required before function {func} can be executed")
        return func(self, *args, **kwargs)

    return inner_func
