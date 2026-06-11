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
class GNS3Exception(Exception):
    """Base class for GNS3 errors."""
    pass

class GNS3UnreachableException(GNS3Exception):
    """GNS3 server is down or unreachable."""
    pass

class GNS3RequestException(GNS3Exception):
    """GNS3 returned an error response."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)