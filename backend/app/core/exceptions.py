class AppError(Exception):
    """Base application exception."""

    status_code: int = 500
    detail: str = "An unexpected application error occurred."

    def __init__(self, detail: str | None = None, status_code: int | None = None) -> None:
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class NotFoundError(AppError):
    """Exception raised when a resource is not found."""

    status_code: int = 404
    detail: str = "The requested resource was not found."


class AuthError(AppError):
    """Exception raised for authentication or authorization failures."""

    status_code: int = 401
    detail: str = "Authentication credentials are invalid or missing."


class ValidationError(AppError):
    """Exception raised for input or request validation failures."""

    status_code: int = 422
    detail: str = "The request parameters or body failed validation."
