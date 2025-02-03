
from uuid import UUID, uuid4
from core.logging import get_logger
from typing import Any, Dict, Optional
from  datetime  import datetime, timezone
from sqlalchemy.exc import IntegrityError
from domain.exceptions import DatabaseError, WorkspaceNotFoundError, WorkspacePermissionError, WorkspaceValidationError
from domain.models.workspaces import Workspace
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class CreateWorkspaceCommand:
    """
    Command for creating a new workspace.
    
    This command handles the creation of a workspace with validation
    and proper error handling.
    """
    async def execute(
            self, 
            session: AsyncSession, 
            title: str,
            description: Optional[str] = None,
            is_completed: bool=False,
            plan_type:str='free',
            settings: Optional[Dict[str, Any]] = None, 
              ) -> Workspace:
        """
        Execute the create workspace command.
        
        Args:
            session: The database session
            title: The workspace title
            description: The workspace description
            plan_type: The plan type (defaults to "free")
            settings: Optional workspace settings
            
        Returns:
            The created workspace instance
            
        Raises:
            WorkspaceValidationError: If validation fails
            IntegrityError: If there's a database constraint violation
        """

        try:
            #create workspace
            workspace = Workspace(
                id=uuid4(),
                title=title,
                description=description, 
                is_completed = is_completed,
                plan_type=plan_type,
                settings=settings or {},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            # Add to session and flush to trigger validation
            session.add(workspace)
            await session.flush()
            
            # Commit the transaction
            await session.commit()
            
            return workspace
            
        except ValueError as e:

            await session.rollback()
            raise WorkspaceValidationError(str(e))
        except IntegrityError as e:
            await session.rollback()
            raise WorkspaceValidationError(f"Database integrity error: {str(e)}")


class UpdateWorkspaceCommand:
    """
    Command for updating an existing workspace.
    
    This command handles the updating of workspace properties with
    proper validation and error handling.
    """

    async def execute(
        self,
        session: AsyncSession,
        workspace_id: uuid4,
        title: Optional[str] = None,
        description: Optional[str] = None,
        plan_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_completed: Optional[bool] = None
    ) -> Optional[Workspace]:
        """
        Execute the update workspace command.
        
        Args:
            session: The database session
            workspace_id: The ID of the workspace to update
            title: Optional new title
            description: Optional new description
            plan_type: Optional new plan type
            settings: Optional new settings
            is_completed: Optional completion status
            
        Returns:
            The updated workspace instance or None if not found
            
        Raises:
            WorkspaceValidationError: If validation fails
            WorkspaceNotFoundError: If the workspace doesn't exist
        """

        try:
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if plan_type is not None:
                update_data["plan_type"] = plan_type
            if settings is not None:
                update_data["settings"] = settings
            if is_completed is not None:
                update_data["is_completed"] = is_completed
                
            if update_data:
                update_data["updated_at"] = datetime.now(timezone.utc)

            workspace = await session.get(Workspace, workspace_id) 

            if not workspace:
                raise WorkspaceNotFoundError(f"Workspace with id {workspace_id} not found")
           
            # Update workspace attributes
            for key, value in update_data.items():
                setattr(workspace, key, value)

            # Flush to trigger validation
            await session.flush()
            
            # Commit the transaction
            await session.commit()
            
            return workspace

        except ValueError as e:
            # Handle validation errors from the model
            await session.rollback()
            raise WorkspaceValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations
            await session.rollback()
            raise WorkspaceValidationError(f"Database integrity error: {str(e)}")


class DeleteWorkspaceCommand:
    """
    Command for deleting an existing workspace.
    
    This command handles the deletion of workspace with proper
    validation and error handling.
    """
    
    async def _check_workspace_exists(
        self,
        session: AsyncSession,
        workspace_id: UUID
    ) -> Workspace:
        """
        Check if workspace exists and return it.
        
        Args:
            session: The database session
            workspace_id: The ID of the workspace to check
            
        Returns:
            The workspace if it exists
            
        Raises:
            WorkspaceNotFoundError: If workspace doesn't exist
        """
        workspace = await session.get(Workspace, workspace_id)
        if not workspace:
            logger.warning(
                "workspace_not_found_for_deletion",
                workspace_id=str(workspace_id)
            )
            raise WorkspaceNotFoundError(
                message=f"Workspace {workspace_id} not found",
                workspace_id=str(workspace_id)
            )
        return workspace

    async def _check_deletion_allowed(
        self,
        workspace: Workspace,
        user_id: Optional[UUID] = None
    ) -> None:
        """
        Check if deletion is allowed for the workspace.
        
        Args:
            workspace: The workspace to check
            user_id: Optional ID of the user attempting deletion
            
        Raises:
            WorkspacePermissionError: If deletion is not allowed
        """
        # Add your business rules for deletion permission here
        # For example:
        if workspace.is_completed:
            logger.warning(
                "cannot_delete_completed_workspace",
                workspace_id=str(workspace.id)
            )
            raise WorkspacePermissionError(
              f"Cannot delete a completed workspace - {workspace.id}",
            )

    async def execute(
        self,
        session: AsyncSession,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
        force: bool = False
    ) -> None:
        """
        Execute the delete workspace command.
        
        Args:
            session: The database session
            workspace_id: The ID of the workspace to delete
            user_id: Optional ID of the user performing the deletion
            force: If True, skip some validation checks
            
        Raises:
            WorkspaceNotFoundError: If workspace doesn't exist
            WorkspacePermissionError: If deletion is not allowed
            DatabaseError: If there's an error during deletion
        """
        try:
            # Check if workspace exists
            workspace = await self._check_workspace_exists(session, workspace_id)
            
            # Check if deletion is allowed (unless force=True)
            if not force:
                await self._check_deletion_allowed(workspace, user_id)

            logger.info(
                "deleting_workspace",
                workspace_id=str(workspace_id),
                user_id=str(user_id) if user_id else None,
                force=force
            )

            # Delete associated records if needed
            # await session.execute(
            #     delete(WorkspaceMembers).where(WorkspaceMembers.workspace_id == workspace_id)
            # )

            # Delete the workspace
            await session.delete(workspace)
            
            # Commit the transaction
            await session.commit()

            logger.info(
                "workspace_deleted_successfully",
                workspace_id=str(workspace_id)
            )

        except IntegrityError as e:
            await session.rollback()
            logger.error(
                "workspace_deletion_integrity_error",
                workspace_id=str(workspace_id),
                error=str(e)
            )
            raise DatabaseError(
                f"Database integrity error while deleting workspace: {str(e)}"
            )
            
        except Exception as e:
            await session.rollback()
            logger.error(
                "workspace_deletion_error",
                workspace_id=str(workspace_id),
                error=str(e)
            )
            raise
