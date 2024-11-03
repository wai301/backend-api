class FirebaseError(Exception):
    """Base exception for Firebase operations"""
    pass

class NotFoundError(FirebaseError):
    """Raised when resource is not found"""
    pass

class DuplicateError(FirebaseError):
    """Raised when resource already exists"""
    pass

class BaseModel:
    """Base class for Firebase models"""
    pass