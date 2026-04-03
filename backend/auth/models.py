"""
ScholarGraph AI — Auth Pydantic Models
Request/Response schemas for authentication endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class TenantCreate(BaseModel):
    name: str
    domain: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
