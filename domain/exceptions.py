class WorkspaceError(Exception):
    """Base exception for workspace-related errors."""
    pass

class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace is not found."""
    pass

class WorkspaceValidationError(WorkspaceError):
    """Raised when workspace validation fails."""
    pass

class WorkspacePermissionError(WorkspaceError):
    """Raised when workspace validation fails."""
    pass

class WorkspaceLimitError(WorkspaceError):
    """Raised when workspace validation fails."""
    pass

class DatabaseError(Exception):
    """Raised when workspace validation fails."""
    pass
