class NetCTRLException(Exception):
    """Base class for all application exceptions."""
    pass


# ==========================
# Authentication
# ==========================

class AuthException(NetCTRLException):
    """Base class for authentication exceptions."""
    pass


class InvalidCredentialsException(AuthException):
    """Raised when authentication fails due to invalid credentials."""
    pass


class UserAlreadyExistsException(AuthException):
    """Raised when a username or email already exists."""
    pass


# ==========================
# Projects
# ==========================

class ProjectException(NetCTRLException):
    """Base class for project-related exceptions."""
    pass


class ProjectNotFoundException(ProjectException):
    """Raised when the requested project does not exist."""
    pass


# ==========================
# GNS3
# ==========================

class GNS3Exception(NetCTRLException):
    """Base class for GNS3-related exceptions."""
    pass


class GNS3UnreachableException(GNS3Exception):
    """Raised when the GNS3 server cannot be reached."""
    pass


class GNS3RequestException(GNS3Exception):
    """Raised when GNS3 returns an error response."""

    def __init__(
        self,
        status_code: int,
        detail: str,
    ):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)