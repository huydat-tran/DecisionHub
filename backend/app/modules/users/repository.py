"""Truy vấn dữ liệu người dùng và vai trò (module Users)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import Role, User


def get_user_by_email(db: Session, email: str) -> User | None:
    """Lấy user theo email, trả về None nếu không tồn tại."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Lấy user theo username, trả về None nếu không tồn tại."""
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()


def get_role_by_name(db: Session, name: str) -> Role | None:
    """Lấy role theo tên (USER, ADMIN)."""
    stmt = select(Role).where(Role.name == name)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, username: str, email: str, password_hash: str, role_id: int) -> User:
    """Tạo tài khoản người dùng mới và flush để lấy id."""
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role_id=role_id,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user
