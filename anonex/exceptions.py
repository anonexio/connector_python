class AnonExError(Exception):
    """Base exception for AnonEx API errors."""
    def __init__(self, message, code=None, description=None):
        self.code = code
        self.description = description
        super().__init__(message)


class AnonExAPIError(AnonExError):
    """API returned an error response."""
    pass


class AnonExAuthError(AnonExError):
    """Authentication failed."""
    pass


class AnonExConnectionError(AnonExError):
    """Connection to the API failed."""
    pass
