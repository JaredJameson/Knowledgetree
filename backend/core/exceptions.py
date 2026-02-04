"""
Custom Exception Classes
Application-specific exceptions for error handling
"""

from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """
    Raised when a requested resource is not found.

    Automatically returns HTTP 404 with custom message.
    """

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ValidationException(HTTPException):
    """
    Raised when input validation fails.

    Automatically returns HTTP 400 with custom message.
    """

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class UnauthorizedException(HTTPException):
    """
    Raised when user is not authenticated.

    Automatically returns HTTP 401.
    """

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(HTTPException):
    """
    Raised when user lacks permission for resource.

    Automatically returns HTTP 403.
    """

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ConflictException(HTTPException):
    """
    Raised when operation conflicts with current state.

    Automatically returns HTTP 409.
    Example: Duplicate resource creation.
    """

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ServiceUnavailableException(HTTPException):
    """
    Raised when external service is unavailable.

    Automatically returns HTTP 503.
    Example: AI service timeout, database connection lost.
    """

    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )
