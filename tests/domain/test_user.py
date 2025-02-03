import pytest
from uuid import UUID
from datetime import datetime, timezone

from domain.models.user import User
from domain.exceptions import ValidationError

class TestUserCreation:
    """Test suite for User model creation and validation."""
    
    def test_basic_creation(self, sample_user_data):
        """Test basic user creation with minimal required fields."""
        user = User(**sample_user_data)
        assert user.email == sample_user_data["email"]
        assert user.name == sample_user_data["name"]
        assert user.password_hash == sample_user_data["password_hash"]
        # assert user.is_active == True
        # assert user.two_factor_enabled == False

    def test_full_creation(self, sample_user_data, current_time):
        """Test user creation with all possible fields."""
        user = User(
            **sample_user_data,
            is_active=False,
            two_factor_enabled=True,
            last_login_at=current_time
        )
        assert user.email == sample_user_data["email"]
        assert user.profile == sample_user_data["profile"]
        assert user.preferences == sample_user_data["preferences"]
        assert user.is_active == False
        assert user.two_factor_enabled == True
        assert user.last_login_at == current_time

class TestUserValidation:
    """Test suite for User model validation rules."""

    def test_email_validation(self, sample_user_data):
        """Test email validation rules."""
        # Empty email
        with pytest.raises(ValueError, match="Email cannot be empty"):
            sample_user_data["email"] = ""
            User(**sample_user_data)

        # Invalid email format
        with pytest.raises(ValueError, match="Invalid email format"):
            sample_user_data["email"] = "invalid_email"
            User(**sample_user_data)

        # Email too long
        with pytest.raises(ValueError, match="Email cannot exceed 255 characters"):
            sample_user_data["email"] = "a" * 247 + "@test.com"
            User(**sample_user_data)

    def test_name_validation(self, sample_user_data):
        """Test name validation rules."""
        # Empty name
        with pytest.raises(ValueError, match="Name cannot be empty"):
            sample_user_data["name"] = ""
            User(**sample_user_data)

        # Name too long
        with pytest.raises(ValueError, match="Name cannot exceed 255 characters"):
            sample_user_data["name"] = "a" * 256
            User(**sample_user_data)

    def test_profile_validation(self, sample_user_data):
        """Test profile validation rules."""
        # Invalid profile type
        with pytest.raises(ValueError, match="Profile must be a dictionary"):
            sample_user_data["profile"] = "invalid"
            User(**sample_user_data)

        # Invalid timezone
        with pytest.raises(ValueError, match="Invalid timezone"):
            sample_user_data["profile"] = {"timezone": 123}
            User(**sample_user_data)

    def test_preferences_validation(self, sample_user_data):
        """Test preferences validation rules."""
        # Invalid preferences type
        with pytest.raises(ValueError, match="Preferences must be a dictionary"):
            sample_user_data["preferences"] = "invalid"
            User(**sample_user_data)

class TestUserMethods:
    """Test suite for User model methods."""

    def test_password_hash_update(self, sample_user_data):
        pass
        """Test password hash update method."""
        # user = User(**sample_user_data)
        # new_hash = "new_hashed_password"
        # user.update_password_hash(new_hash)
        # assert user.password_hash == new_hash

    def test_last_login_update(self, sample_user_data, current_time):
        pass
        """Test last login update method."""
        # user = User(**sample_user_data)
        # user.update_last_login(current_time)
        # assert user.last_login_at == current_time

class TestUserRelationships:
    """Test suite for User model relationships."""

    def test_workspace_memberships(self, sample_user_data):
        """Test workspace memberships relationship."""
        user = User(**sample_user_data)
        assert hasattr(user, 'workspace_memberships')
        assert len(user.workspace_memberships) == 0

    def test_team_memberships(self, sample_user_data):
        """Test team memberships relationship."""
        user = User(**sample_user_data)
        assert hasattr(user, 'team_memberships')
        assert len(user.team_memberships) == 0

class TestUserEdgeCases:
    """Test suite for User model edge cases."""

    def test_empty_profile(self, sample_user_data):
        """Test user creation with empty profile."""
        sample_user_data["profile"] = {}
        user = User(**sample_user_data)
        assert user.profile == {}

    def test_none_preferences(self, sample_user_data):
        """Test user creation with None preferences."""
        sample_user_data["preferences"] = None
        user = User(**sample_user_data)
        assert user.preferences == {}

    def test_special_characters_in_email(self, sample_user_data):
        """Test user creation with special characters in email."""
        sample_user_data["email"] = "test.user+label@example.com"
        user = User(**sample_user_data)
        assert user.email == "test.user+label@example.com"

@pytest.mark.asyncio
class TestUserAsync:
    """Test suite for User model async operations."""

    async def test_get_teams_async(self, sample_user_data):
        pass
        """Test getting user teams asynchronously."""
        # user = User(**sample_user_data)
        # teams = await user.get_teams()
        # assert isinstance(teams, list)

    async def test_get_workspaces_async(self, sample_user_data):
        """Test getting user workspaces asynchronously."""
        pass
        # user = User(**sample_user_data)
        # workspaces = await user.get_workspaces()
        # assert isinstance(workspaces, list)