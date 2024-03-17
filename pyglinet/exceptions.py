class AccessDeniedError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NotLoggedInError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LoggedInError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WrongParametersError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MethodNotFoundError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class KeepAliveThreadActiveError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WrongApiDescriptionError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UnsupportedHashAlgoError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
