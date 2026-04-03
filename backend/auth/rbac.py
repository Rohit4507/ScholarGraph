"""
ScholarGraph AI — Role-Based Access Control (RBAC)
Dependency injection decorators for role-based route protection.
"""

from functools import wraps
from typing import List
from fastapi import Depends, HTTPException, status
from database.models import User
from auth.jwt_handler import get_current_user


class RoleChecker:
    """Dependency class that verifies user has required role."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}",
            )
        return user


# ── Pre-built Role Dependencies ─────────────────────────────────
require_student = RoleChecker(["student", "professor", "admin"])
require_professor = RoleChecker(["professor", "admin"])
require_admin = RoleChecker(["admin"])
require_any = RoleChecker(["student", "professor", "admin"])
