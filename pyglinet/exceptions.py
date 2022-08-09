class AccessDeniedError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NotLoggedInError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LoggedInError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
