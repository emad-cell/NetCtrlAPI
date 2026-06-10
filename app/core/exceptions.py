class AuthException(Exception):
    """Base class for authentication exceptions."""
    pass

class InvalidCredentialsException(AuthException):
    """Raised when authentication fails due to invalid credentials."""
    pass

class UserAlreadyExistsException(AuthException):
    """Raised when registering a user that already exists (email or username)."""
    pass

class ProjectNotFoundException(Exception):
    pass