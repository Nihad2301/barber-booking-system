class AppException(Exception):
    """Base exception class for custom application errors"""
    status_code: int
    default_message: str

    def __init__(self, message: str = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidCredentialsError(AppException):
    status_code = 401
    default_message = "Invalid credentials"


class InvalidCodeError(AppException):
    status_code = 400
    default_message = "Invalid verification code"


class ExpiredCodeError(AppException):
    status_code = 400
    default_message = "Verification code has expired"


class ExpiredTokenError(AppException):
    status_code = 401
    default_message = "Token has expired"


class InvalidTokenError(AppException):
    status_code = 401
    default_message = "Invalid token"


class EmailNotVerifiedError(AppException):
    status_code = 403
    default_message = "Email not verified"


class AlreadyExistsError(AppException):
    status_code = 409
    default_message = "Resource already exists"


class ForbiddenError(AppException):
    status_code = 403
    default_message = "Access forbidden"


class NotFoundError(AppException):
    status_code = 404
    default_message = "Resource not found"


class AlreadyClaimedError(AppException):
    status_code = 409
    default_message = "Slot already claimed"
