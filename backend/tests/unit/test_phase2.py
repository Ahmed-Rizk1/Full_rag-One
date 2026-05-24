import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository


@pytest.mark.asyncio
async def test_user_repository_crud(db_session: AsyncSession):
    """Test standard CRUD operations via BaseRepository and UserRepository."""
    user_repo = UserRepository()

    # 1. Test Create
    user_in = {
        "email": "test_user@example.com",
        "hashed_password": "hashed_secret_password",
        "full_name": "Test User",
        "role": "user",
    }
    user = await user_repo.create(db_session, obj_in=user_in)
    assert user.id is not None
    assert user.email == "test_user@example.com"
    assert user.full_name == "Test User"
    assert user.role == "user"
    assert user.created_at is not None
    assert user.updated_at is not None

    # 2. Test Get (Read by ID)
    fetched_user = await user_repo.get(db_session, id=user.id)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.email == user.email

    # 3. Test Get By Email (Specialized method)
    fetched_by_email = await user_repo.get_by_email(db_session, email="test_user@example.com")
    assert fetched_by_email is not None
    assert fetched_by_email.id == user.id

    fetched_missing_email = await user_repo.get_by_email(db_session, email="nonexistent@example.com")
    assert fetched_missing_email is None

    # 4. Test Update
    update_data = {"full_name": "Updated User Name", "role": "admin"}
    updated_user = await user_repo.update(db_session, db_obj=user, obj_in=update_data)
    assert updated_user.full_name == "Updated User Name"
    assert updated_user.role == "admin"

    # 5. Test Get Multi
    users_list = await user_repo.get_multi(db_session, skip=0, limit=10)
    assert len(users_list) == 1
    assert users_list[0].id == user.id

    # 6. Test Delete
    deleted_user = await user_repo.delete(db_session, id=user.id)
    assert deleted_user is not None
    assert deleted_user.id == user.id

    # Verify database no longer contains user
    not_found_user = await user_repo.get(db_session, id=user.id)
    assert not_found_user is None
